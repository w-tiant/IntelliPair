import json
from collections import Counter
import pandas as pd
import random
import heapq
import csv
from tqdm import tqdm
import os
import numpy as np
import time
import math

import dgl
import dgl.nn as dglnn
import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl.function as fn
from dgl.utils import expand_as_pair
from dgl.nn.functional import edge_softmax

from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, accuracy_score

from dgl.sampling import RandomWalkNeighborSampler
from torch.utils.data import DataLoader 


os.environ['CUDA_VISIBLE_DEVICES'] = '1' 
device = ("cuda" if torch.cuda.is_available() else "cpu")

dataset_folder = '../data/LargeRG/'
ckpt_folder = '../data/LargeRG/'
tuned_emb_file = 'pretrained_image_emb.pt'

# 1. 图构建 ------------------------------------------------

def get_graph():
    print('generating graph ...')
    all_r2i_src_dst, train_r2i_src_dst, val_r2i_src_dst, test_r2i_src_dst = torch.load(dataset_folder+'r2i_all_train_val_test_src_dst.pt')
    r2i_edge_src, r2i_edge_dst = all_r2i_src_dst
    r2r_edge_src, r2r_edge_dst, r2r_edge_weight = torch.load(dataset_folder+'r2r_edge_src_dst_weight.pt')
    i2i_edge_src, i2i_edge_dst, i2i_edge_weight = torch.load(dataset_folder+'/i2i_edge_src_dst_weight.pt')
    all_u2r_src_dst_weight, train_u2r_src_dst_weight, val_u2r_src_dst_weight, test_u2r_src_dst_weight = torch.load(dataset_folder+'u2r_all_train_val_test_src_dst_weight.pt')
    u2r_edge_src, u2r_edge_dst, u2r_edge_weight = all_u2r_src_dst_weight

    graph = dgl.heterograph({
        ('recipe', 'r-i', 'ingredient'): (r2i_edge_src, r2i_edge_dst),
        ('ingredient', 'i-r', 'recipe'): (r2i_edge_dst, r2i_edge_src),
        ('recipe', 'r-r', 'recipe'): (r2r_edge_src, r2r_edge_dst),
        ('ingredient', 'i-i', 'ingredient'): (i2i_edge_src, i2i_edge_dst),
        ('user', 'u-r', 'recipe'): (u2r_edge_src, u2r_edge_dst),
        ('recipe', 'r-u', 'user'): (u2r_edge_dst, u2r_edge_src)
    })

    graph.edges['r-r'].data['weight'] = torch.FloatTensor(r2r_edge_weight)
    graph.edges['i-i'].data['weight'] = torch.FloatTensor(i2i_edge_weight)
    graph.edges['u-r'].data['weight'] = torch.FloatTensor(u2r_edge_weight)
    graph.edges['r-u'].data['weight'] = torch.FloatTensor(u2r_edge_weight)
    graph.edges['r-i'].data['weight'] = torch.ones(len(r2i_edge_src))
    graph.edges['i-r'].data['weight'] = torch.ones(len(r2i_edge_src))
    
    recipe_nodes_avg_instruction_features = torch.load(dataset_folder+'/recipe_nodes_instruction_features.pt')
    ingredient_nodes_nutrient_features = torch.load(dataset_folder+'/ingredient_nodes_nutrient_features.pt')
    recipe_nodes_pretraind_image_features = torch.load(ckpt_folder + tuned_emb_file)
    graph.nodes['recipe'].data['avg_instr_feature'] = recipe_nodes_avg_instruction_features
    graph.nodes['ingredient'].data['nutrient_feature'] = ingredient_nodes_nutrient_features
    graph.nodes['recipe'].data['resnet_image'] = recipe_nodes_pretraind_image_features
    graph.nodes['user'].data['random_feature'] = torch.nn.init.xavier_normal_(torch.ones(graph.num_nodes('user'), 300))
    
    train_mask = torch.load(dataset_folder+'/train_cuisine_mask.pt')
    val_mask = torch.load(dataset_folder+'/val_cuisine_mask.pt')
    test_mask = torch.load(dataset_folder+'/test_cuisine_mask.pt')
    recipe_nodes_labels = torch.load(dataset_folder+'/recipe_nodes_cuisine_labels.pt')
    graph.nodes['recipe'].data['train_mask'] = train_mask
    graph.nodes['recipe'].data['val_mask'] = val_mask
    graph.nodes['recipe'].data['test_mask'] = test_mask
    graph.nodes['recipe'].data['label'] = recipe_nodes_labels.long()

    return graph

graph = get_graph()
print('graph: ', graph)

def get_train_val_test_idx():
    train_mask = graph.nodes['recipe'].data['train_mask']
    val_mask = graph.nodes['recipe'].data['val_mask']
    test_mask = graph.nodes['recipe'].data['test_mask']

    train_idx = torch.nonzero(train_mask, as_tuple=False).squeeze()
    val_idx = torch.nonzero(val_mask, as_tuple=False).squeeze()
    test_idx = torch.nonzero(test_mask, as_tuple=False).squeeze()
    
    return train_idx, val_idx, test_idx

train_idx, val_idx, test_idx = get_train_val_test_idx()
print('length of train_idx: ', len(train_idx))
print('length of val_idx: ', len(val_idx))
print('length of test_idx: ', len(test_idx))

# 2. 模型定义 ------------------------------------------------

def norm(input, p=1, dim=1, eps=1e-12):
    return input / input.norm(p, dim, keepdim=True).clamp(min=eps).expand_as(input)

class custom_GINConv(nn.Module):
    # 结合了注意力的 GINConv
    def __init__(self, apply_func, aggregator_type, init_eps=0, learn_eps=False):
        super(custom_GINConv, self).__init__()
        self.apply_func = apply_func
        self._aggregator_type = aggregator_type
        
        if aggregator_type == 'sum': self._reducer = fn.sum
        elif aggregator_type == 'max': self._reducer = fn.max
        elif aggregator_type == 'mean': self._reducer = fn.mean
        else: raise KeyError('Aggregator type {} not recognized.'.format(aggregator_type))
        
        if learn_eps: self.eps = torch.nn.Parameter(torch.FloatTensor([init_eps]))
        else: self.register_buffer('eps', torch.FloatTensor([init_eps]))
        
        self.fc_src = nn.Linear(128, 128, bias=False)
        self.fc_dst = nn.Linear(128, 128, bias=False)
        self.attn_l = nn.Parameter(torch.FloatTensor(size=(1, 128)))
        self.attn_r = nn.Parameter(torch.FloatTensor(size=(1, 128)))
        self.negative_slope = 0.2
        self.leaky_relu = nn.LeakyReLU(self.negative_slope)
        self.attn_drop = nn.Dropout(0)
        self.fc_src2 = nn.Linear(128, 128, bias=False)
        self.fc_dst2 = nn.Linear(128, 128, bias=False)
        gain = nn.init.calculate_gain('relu')
        
        nn.init.xavier_normal_(self.fc_src.weight, gain=gain)
        nn.init.xavier_normal_(self.fc_dst.weight, gain=gain)
        nn.init.xavier_normal_(self.attn_l, gain=gain)
        nn.init.xavier_normal_(self.attn_r, gain=gain)

    def forward(self, graph, feat, edge_weight=None):
        # 兼容异构输入
        if isinstance(feat, dict):
            feat = feat.get('recipe', next(iter(feat.values())))

        with graph.local_scope():
            feat_src_original, feat_dst_original = expand_as_pair(feat, graph)
            
            # --- 用于两条信息流的特征 ---
            feat_src1 = self.fc_src(feat_src_original)
            feat_dst1 = self.fc_dst(feat_dst_original)
            feat_src2 = self.fc_src2(feat_src_original)
            feat_dst2 = self.fc_dst2(feat_dst_original)
            
            # --- 1. 注意力权重 ---
            el = (feat_src2 * self.attn_l).sum(dim=-1, keepdim=True)
            er = (feat_dst2 * self.attn_r).sum(dim=-1, keepdim=True)
            graph.srcdata.update({'el': el})
            graph.dstdata.update({'er': er})
            graph.apply_edges(fn.u_add_v('el', 'er', 'e'))
            e = self.leaky_relu(graph.edata.pop('e'))
            graph.edata['a'] = self.attn_drop(edge_softmax(graph, e))

            # --- 2. 信息流聚合 ---
            
            # --- 一: 主干GIN逻辑 ---
            graph.srcdata['h_main'] = feat_src1
            graph.update_all(fn.copy_u('h_main', 'm_main'),
                             self._reducer('m_main', 'neigh'))

            # --- 二: 注意力增强逻辑 ---
            graph.srcdata['feat_src2'] = feat_src2
            graph.update_all(fn.u_mul_e('feat_src2', 'a', 'm_attn'),
                             fn.sum('m_attn', 'add_ft'))
            
            # --- 3. 结果 ---
            # 检查 add_ft 是否存在
            if 'add_ft' not in graph.dstdata:
                graph.dstdata['add_ft'] = torch.zeros_like(graph.dstdata['neigh'])

            rst = (1 + self.eps) * feat_dst1 + graph.dstdata['neigh'] + graph.dstdata['add_ft']
            
            if self.apply_func is not None:
                rst = self.apply_func(rst)
            return rst

class StochasticTwoLayerRGCN(nn.Module):
    def __init__(self, in_feat, hidden_feat, out_feat, rel_names):
        super().__init__()
        self.conv1 = dglnn.HeteroGraphConv({
                rel : dglnn.GraphConv(in_feat, hidden_feat, norm='right')
                for rel in rel_names
            }, aggregate='sum')
    def forward(self, blocks, x):
        x = self.conv1(blocks, x)
        return x
    
class RelationAttention(nn.Module):
    def __init__(self, in_size, hidden_size=128):
        super(RelationAttention, self).__init__()
        self.project = nn.Sequential(nn.Linear(in_size, hidden_size), nn.Tanh(), nn.Linear(hidden_size, 1, bias=False))
    def forward(self, z):
        w = self.project(z).mean(0)
        beta = torch.softmax(w, dim=0)
        beta = beta.expand((z.shape[0],) + beta.shape)
        out = (beta * z).sum(1)
        return out
    
global_h_list_instr = graph.nodes['recipe'].data['avg_instr_feature'].to(device)
global_h_list_image = graph.nodes['recipe'].data['resnet_image'].to(device)

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.user_embedding = nn.Sequential(nn.Linear(300, 128), nn.ReLU())
        self.ingredient_embedding = nn.Sequential(nn.Linear(46, 128), nn.ReLU())
        
        self.metapath_gin = custom_GINConv(nn.Linear(128, 128), 'max')
        
        self.rgcn = StochasticTwoLayerRGCN(128, 128, 128, graph.etypes)
        self.encoder_instr = nn.Sequential(nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU())
        self.encoder_image = nn.Sequential(nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU())
        
        self.cross_view_out = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
        )
        
        self.out = nn.Sequential(nn.Linear(128, 9))
        self.relation_attention = RelationAttention(128)

    def forward(self, blocks, input_features, seeds, adv_deltas):
        user, avg_instr, ingredient, image = input_features
        
        # --- 1. 特征编码 ---
        user_emb = self.user_embedding(user)
        ingredient_emb = self.ingredient_embedding(ingredient)
        instr_emb = self.encoder_instr(avg_instr)
        image_emb = self.encoder_image(image)
        
        # --- 2. 嵌入空间中加入扰动 ---
        if adv_deltas:
            delta_user, delta_instr, delta_ingredient, delta_image = adv_deltas
            user_emb += delta_user
            instr_emb += delta_instr
            ingredient_emb += delta_ingredient
            image_emb += delta_image

        user_emb = norm(user_emb)
        ingredient_emb = norm(ingredient_emb)
        instr_emb = norm(instr_emb)
        image_emb = norm(image_emb)

        # --- 3. Schema-based GNN (主体) ---
        h_dict_instr = {'user': user_emb, 'recipe': instr_emb, 'ingredient': ingredient_emb}
        x1 = self.rgcn(blocks[-1], h_dict_instr)['recipe']
        
        h_dict_image = {'user': user_emb, 'recipe': image_emb, 'ingredient': ingredient_emb}
        x2 = self.rgcn(blocks[-1], h_dict_image)['recipe']
        
        # --- 4. Metapath-based GNN ---
        src_nodes_for_mp = blocks[0].srcdata[dgl.NID]
        src_features_instr_for_mp = self.encoder_instr(global_h_list_instr[src_nodes_for_mp])
        src_features_image_for_mp = self.encoder_image(global_h_list_image[src_nodes_for_mp])
        
        # 在metapath块上GIN卷积
        h1_instr = self.metapath_gin(blocks[0], src_features_instr_for_mp)
        h1_image = self.metapath_gin(blocks[0], src_features_image_for_mp)

        # --- 5. 最终融合 ---
        x1 = x1.unsqueeze(1)
        x2 = x2.unsqueeze(1)
        h1_instr = h1_instr.unsqueeze(1)
        h1_image = h1_image.unsqueeze(1)
        
        # [batch_size, 1, 512]
        concatenated_features = torch.cat([x1, x2, h1_instr, h1_image], dim=2)
        # [batch_size, 1, 128]
        x = self.cross_view_out(concatenated_features)
        x = self.relation_attention(x)
        
        return self.out(x), x

metapath_list = [['r-u', 'u-r']]

class HANSampler(object):
    def __init__(self, g, metapath_list, num_neighbors):
        self.g = g
        self.sampler_list = []
        for metapath in metapath_list:
            self.sampler_list.append(RandomWalkNeighborSampler(
                G=g, num_traversals=1, # 简化traversal，匹配原代码的单层metapath
                termination_prob=0,
                num_random_walks=num_neighbors,
                num_neighbors=num_neighbors,
                metapath=metapath))
        self.schema_sampler = dgl.dataloading.MultiLayerNeighborSampler([10])

    def sample_blocks(self, seeds):
        seeds = torch.LongTensor(seeds)
        block_list = []
        
        # Metapath sampling
        frontier = self.sampler_list[0](seeds)
        block = dgl.to_block(frontier, seeds)
        block_list.append(block)
        
        # Schema sampling
        schema_dataloader = dgl.dataloading.DataLoader(
            self.g, {'recipe': seeds}, self.schema_sampler,
            batch_size=len(seeds), shuffle=False, drop_last=False, num_workers=0)
        _, _, schema_blocks = next(iter(schema_dataloader))
        block_list.append(schema_blocks[0])

        return seeds, block_list
    
# 3. 训练 ------------------------------------------------

han_sampler = HANSampler(graph, metapath_list, num_neighbors=5)

train_dataloader = DataLoader(
    dataset=train_idx.cpu(), batch_size=4096,
    collate_fn=han_sampler.sample_blocks, shuffle=True,
    drop_last=False, num_workers=0) # num_workers=0 保证稳定

val_dataloader = DataLoader(
    dataset=val_idx.cpu(), batch_size=4096,
    collate_fn=han_sampler.sample_blocks, shuffle=False,
    drop_last=False, num_workers=0)

test_dataloader = DataLoader(
    dataset=test_idx.cpu(), batch_size=4096,
    collate_fn=han_sampler.sample_blocks, shuffle=False,
    drop_last=False, num_workers=0)


def get_score(y_pred, y_true):
    total_acc = accuracy_score(y_true, y_pred)
    score = { "f1": f1_score(y_true, y_pred, average='micro'), "acc": total_acc }
    matrix = confusion_matrix(y_true, y_pred)
    detailed_acc = matrix.diagonal()/matrix.sum(axis=1) if np.all(matrix.sum(axis=1) > 0) else np.zeros_like(matrix.diagonal(), dtype=float)
    detailed_score = { "f1": f1_score(y_true, y_pred, average=None, zero_division=0), "acc": detailed_acc }
    return score, detailed_score

def evaluate(model, dataloader, device):
    model.eval()
    total_loss = 0
    all_y_preds, all_labels = [], []

    with torch.no_grad():
        for seeds, blocks in dataloader:
            blocks = [b.to(device) for b in blocks]

            input_user = blocks[-1].srcdata['random_feature']['user']
            input_instr = blocks[-1].srcdata['avg_instr_feature']['recipe']
            input_ingredient = blocks[-1].srcdata['nutrient_feature']['ingredient']
            input_image = blocks[-1].srcdata['resnet_image']['recipe']
            
            labels = blocks[-1].dstdata['label']['recipe']
            inputs = [input_user, input_instr, input_ingredient, input_image]
            logits, _ = model(blocks, inputs, seeds, None)
            all_y_preds.append(torch.argmax(logits, dim=1).cpu())
            all_labels.append(labels.cpu())
            
            loss = criterion(logits, labels)
            total_loss += loss.item() * len(seeds)

    all_y_preds = torch.cat(all_y_preds).numpy()
    all_labels = torch.cat(all_labels).numpy()
    total_score, detailed_score = get_score(all_y_preds, all_labels)
    return total_loss / len(all_labels), total_score['f1'], total_score['acc'], detailed_score['f1'], detailed_score['acc']

def get_PGD_inputs(model, blocks, inputs, labels, seeds, eps=0.02, alpha=0.005, iters=5):
    user, instr, ingredient, image = inputs
    
    user_clone = user.clone().detach()
    instr_clone = instr.clone().detach()
    ingredient_clone = ingredient.clone().detach()
    image_clone = image.clone().detach()
    
    delta_user = torch.nn.Parameter((torch.rand_like(user_clone) * 2 - 1) * eps)
    delta_instr = torch.nn.Parameter((torch.rand_like(instr_clone) * 2 - 1) * eps)
    delta_ingredient = torch.nn.Parameter((torch.rand_like(ingredient_clone) * 2 - 1) * eps)
    delta_image = torch.nn.Parameter((torch.rand_like(image_clone) * 2 - 1) * eps)

    for i in range(iters):
        # 被扰动后的输入
        perturbed_inputs = [user_clone + delta_user, instr_clone + delta_instr, ingredient_clone + delta_ingredient, image_clone + delta_image]
        logits, _ = model(blocks, perturbed_inputs, seeds, None) # 这里adv_deltas传None
        
        model.zero_grad()
        loss = criterion(logits, labels)
        loss.backward()
        
        with torch.no_grad():
            delta_user.data = torch.clamp(delta_user.data + alpha * delta_user.grad.sign(), -eps, eps)
            delta_instr.data = torch.clamp(delta_instr.data + alpha * delta_instr.grad.sign(), -eps, eps)
            delta_ingredient.data = torch.clamp(delta_ingredient.data + alpha * delta_ingredient.grad.sign(), -eps, eps)
            delta_image.data = torch.clamp(delta_image.data + alpha * delta_image.grad.sign(), -eps, eps)

        delta_user.grad.zero_(); delta_instr.grad.zero_();
        delta_ingredient.grad.zero_(); delta_image.grad.zero_()

    return [delta_user.detach(), delta_instr.detach(), delta_ingredient.detach(), delta_image.detach()]


model = Model().to(device)
opt = torch.optim.Adam(model.parameters(), lr=0.005)
scheduler = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.95)
criterion = nn.CrossEntropyLoss().to(device)

print('Start training...')

for epoch in range(100):

    print(f"\n--- Epoch {epoch+1}/{100} ---")
    train_start = time.time()
    model.train()
    epoch_loss = 0

    for batch, (seeds, blocks) in enumerate(tqdm(train_dataloader, desc=f"Epoch {epoch+1}/100")):
        blocks = [b.to(device) for b in blocks]
        
        input_user = blocks[-1].srcdata['random_feature']['user']
        input_instr = blocks[-1].srcdata['avg_instr_feature']['recipe']
        input_ingredient = blocks[-1].srcdata['nutrient_feature']['ingredient']
        input_image = blocks[-1].srcdata['resnet_image']['recipe']
        labels = blocks[-1].dstdata['label']['recipe']
        inputs = [input_user, input_instr, input_ingredient, input_image]
        
        logits, x = model(blocks, inputs, seeds, None)
        
        adv_deltas = get_PGD_inputs(model, blocks, inputs, labels, seeds)
        adv_inputs = [inputs[0]+adv_deltas[0], inputs[1]+adv_deltas[1], inputs[2]+adv_deltas[2], inputs[3]+adv_deltas[3]]
        adv_logits, adv_x = model(blocks, adv_inputs, seeds, None)
        
        adversarial_loss = criterion(adv_logits, labels)
        loss = criterion(logits, labels) + 0.1 * adversarial_loss
        
        opt.zero_grad()
        loss.backward()
        opt.step()
        epoch_loss += loss.item()
    
    scheduler.step()
    
    val_loss, val_f1, val_acc, _, _ = evaluate(model, val_dataloader, device)
    train_end = time.time()
    
    print(f"Epoch {epoch+1:03d} | Train Loss: {epoch_loss/len(train_dataloader):.4f} | Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f} | Val Acc: {val_acc:.4f} | Time: {train_end-train_start:.2f}s")

test_loss, test_f1, test_acc, test_detailed_f1, test_detailed_acc = evaluate(model, test_dataloader, device)
print(f"\nFinal Test Results:")
print(f"Test Loss: {test_loss:.4f} | Test F1: {test_f1:.4f} | Test Acc: {test_acc:.4f}")

# 4. 保存 ------------------------------------------------

print("\n" + "="*80)
print("Saving final assets...")
print("="*80)

# --- 1. 保存映射字典 ---
try:
    _, nodeID2ingreID_dict = torch.load(dataset_folder + 'ingre2nodeID_and_nodeID2ingre.pt')
    py_nodeID2ingreID_dict = {int(k): int(v) for k, v in nodeID2ingreID_dict.items()}
    with open('ingredient_mapping.json', 'w') as f:
        json.dump(py_nodeID2ingreID_dict, f)
    print("--> [SUCCESS1] 'ingredient_mapping.json' saved.")
except Exception as e:
    print(f"--> [ERROR1]: {e}")

# --- 2. 保存嵌入 ---
model.eval()
final_embeddings = {}
with torch.no_grad():
    all_node_types = graph.ntypes
    for ntype in all_node_types:
        node_ids = graph.nodes(ntype).to(device)
        if ntype == 'user':
            features = model.user_embedding(graph.nodes['user'].data['random_feature'].to(device))
        elif ntype == 'ingredient':
            features = model.ingredient_embedding(graph.nodes['ingredient'].data['nutrient_feature'].to(device))
        elif ntype == 'recipe':
            instr_feat = model.encoder_instr(graph.nodes['recipe'].data['avg_instr_feature'].to(device))
            image_feat = model.encoder_image(graph.nodes['recipe'].data['resnet_image'].to(device))
            features = (instr_feat + image_feat) / 2 # 简化融合
        else:
            continue
        
        final_embeddings[ntype] = features.cpu().numpy()
        print(f"--> [SUCCESS2] '{ntype}' embeddings (pre-GNN), shape: {final_embeddings[ntype].shape}")

if 'ingredient' in final_embeddings:
    np.save('ingredient_embeddings.npy', final_embeddings['ingredient'])
    print("--> [SUCCESS3] 'ingredient_embeddings.npy' saved.")
else:
    print("--> [ERROR3]")

print("="*80)
print("Done!")
print("="*80)