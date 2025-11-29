
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import json

# --- 配置 ---
FLAVOR_NET_DIR = Path("./data/flavor_network_data")
LARGE_RG_DIR = Path("./data")

# 输出文件
OUTPUT_MAP_FILE = Path("./i18n/alignment_map.json")
OUTPUT_EMBEDDINGS_FILE = LARGE_RG_DIR / "aligned_multimodal_embeddings.npy"

# LargeRG 预处理文件
LRG_EMBEDDINGS_PATH = LARGE_RG_DIR / "ingredient_english_embeddings.npy"
LRG_NAMES_PATH = LARGE_RG_DIR / "large_rg_ingredient_names.txt"

def align_and_inject():
    print("--- 开始对齐与注入流程 ---")
    
    # 1. 加载 flavor_network 数据
    ingr_info_df = pd.read_csv(
        FLAVOR_NET_DIR / "ingr_comp" / "ingr_info.tsv", 
        sep='\t', header=None, names=['id', 'name', 'category'], skiprows=1
    )
    ingr_info_df['id'] = pd.to_numeric(ingr_info_df['id'])
    ingr_info_df.sort_values('id', inplace=True)
    target_names = ingr_info_df['name'].tolist()
    print(f"加载了 {len(target_names)} 种 flavor_network 食材 (目标)。")

    # 2. 加载 LargeRG
    large_rg_embeddings = np.load(LRG_EMBEDDINGS_PATH)
    with open(LRG_NAMES_PATH, 'r', encoding='utf-8') as f:
        large_rg_names = [line.strip() for line in f]
    large_rg_name_to_idx = {name: i for i, name in enumerate(large_rg_names)}
    print(f"加载了 {len(large_rg_names)} 个 LargeRG 食材嵌入 (源)。")

    # 3. 实体对齐
    alignment_map = {}
    print("正在进行实体对齐...")
    for fn_name in tqdm(target_names, desc="Aligning"):
        cleaned_fn_name = fn_name.replace('_', ' ').lower()
        
        if cleaned_fn_name in large_rg_name_to_idx:
            alignment_map[fn_name] = cleaned_fn_name
            continue
        
    print(f"对齐完成！成功匹配 {len(alignment_map)} 种食材。")

    # 4. 特征注入
    embedding_dim = large_rg_embeddings.shape[1]
    aligned_embeddings = np.zeros((len(target_names), embedding_dim), dtype=np.float32)
    
    found_count = 0
    print("正在注入特征...")
    for i, target_name in enumerate(tqdm(target_names, desc="Injecting")):
        large_rg_name = alignment_map.get(target_name)
        if large_rg_name:
            source_idx = large_rg_name_to_idx.get(large_rg_name)
            if source_idx is not None:
                aligned_embeddings[i] = large_rg_embeddings[source_idx]
                found_count += 1
    print(f"注入完成！成功为 {found_count} 种食材注入特征。")
    
    # 5. 保存产出
    np.save(OUTPUT_EMBEDDINGS_FILE, aligned_embeddings)
    print(f"已对齐的嵌入文件已保存到: {OUTPUT_EMBEDDINGS_FILE}")

    with open(OUTPUT_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(alignment_map, f, ensure_ascii=False, indent=2)
    print(f"对齐映射已保存到: {OUTPUT_MAP_FILE}")

if __name__ == "__main__":
    align_and_inject()