
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from itertools import combinations
from collections import defaultdict

def calculate_flavor_similarity(ingr_comp_dict: dict, ingr_info_df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有食材之间基于共享风味化合物的Jaccard相似度矩阵。

    Args:
        ingr_comp_dict (dict): 食材ID到其风味化合物集合的映射 {ingr_id: {comp_id_1, ...}}。
        ingr_info_df (pd.DataFrame): 食材信息 DataFrame，用于获取完整的食材列表。

    Returns:
        pd.DataFrame: 一个N x N的DataFrame，其中N是食材总数，值为0到1的Jaccard相似度分数。
                      行和列的索引都是食材的名称。
    """
    print("\n--- 开始计算创新探索 (风味) 相似度矩阵... ---")
    
    # 用食材名称作为索引
    id_to_name = pd.Series(ingr_info_df.name.values, index=ingr_info_df.id).to_dict()
    all_ingredient_ids = list(ingr_info_df['id'])
    
    # np.float32节省内存
    similarity_matrix = pd.DataFrame(
        np.zeros((len(all_ingredient_ids), len(all_ingredient_ids)), dtype=np.float32),
        index=[id_to_name[i] for i in all_ingredient_ids],
        columns=[id_to_name[i] for i in all_ingredient_ids]
    )

    # combinations避免重复计算 (A,B) 和 (B,A)
    for id1, id2 in combinations(all_ingredient_ids, 2):
        set1 = ingr_comp_dict.get(id1, set())
        set2 = ingr_comp_dict.get(id2, set())
        
        intersection = len(set1.intersection(set2))
        if intersection == 0:
            continue # 如果没有交集，相似度为0，跳过

        union = len(set1.union(set2))
        jaccard_sim = intersection / union if union != 0 else 0
        
        name1 = id_to_name[id1]
        name2 = id_to_name[id2]
        similarity_matrix.loc[name1, name2] = jaccard_sim
        similarity_matrix.loc[name2, name1] = jaccard_sim

    # 对角线填充为1
    np.fill_diagonal(similarity_matrix.values, 1.0)
    
    print("--- 风味相似度矩阵计算完成! ---")
    return similarity_matrix


def calculate_cooccurrence_similarity(recipes_list_of_sets: list, ingr_info_df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有食材之间基于食谱共现的余弦相似度矩阵。
    此版本已更新，可以直接处理包含食材标准名称集合的列表。

    Args:
        recipes_list_of_sets (list): 一个食谱列表，其中每个食谱是一个包含食材标准名称的集合。
        ingr_info_df (pd.DataFrame): 食材信息 DataFrame。

    Returns:
        pd.DataFrame: 一个N x N的DataFrame，值为余弦相似度分数。
                      行和列的索引都是食材的名称。
    """
    print("\n--- 开始计算经典搭配 (共现) 相似度矩阵... ---")
    print("步骤 1/3: 创建 食谱-食材 的关系列表...")

    # 获取所有食材的标准名称列表，这将作为我们矩阵的最终索引和列
    all_ingredient_names = ingr_info_df['name'].tolist()
    
    # 我们不再需要 recipe_id，而是使用列表的索引 (0, 1, 2...) 作为食谱的唯一标识
    # 我们将创建一个长格式的列表，用于后续的 DataFrame 构建
    recipe_indices = []
    ingredient_names = []
    
    for recipe_idx, ingredients_set in enumerate(recipes_list_of_sets):
        for ingr_name in ingredients_set:
            recipe_indices.append(recipe_idx)
            ingredient_names.append(ingr_name)

    # 创建一个包含所有共现信息的长格式DataFrame
    cooccurrence_df = pd.DataFrame({
        'recipe_idx': recipe_indices,
        'ingredient_name': ingredient_names
    })
    
    # 确保没有无效的食材名混入
    cooccurrence_df = cooccurrence_df[cooccurrence_df['ingredient_name'].isin(all_ingredient_names)]
    
    # 使用crosstab来创建 食谱 x 食材 的矩阵
    # 值是食材在食谱中出现的次数（在这里都是1）
    recipe_ingredient_matrix = pd.crosstab(
        cooccurrence_df['recipe_idx'], 
        cooccurrence_df['ingredient_name']
    )
    
    # 确保矩阵的列包含了所有已知的食材，并按正确的顺序排列
    recipe_ingredient_matrix = recipe_ingredient_matrix.reindex(
        columns=all_ingredient_names, fill_value=0
    )
    
    print("步骤 2/3: 计算余弦相似度 (这可能需要一些时间)...")
    # 计算食材(列)之间的余弦相似度
    # .T 表示转置矩阵，因为cosine_similarity默认计算行之间的相似度
    cosine_sim_matrix = cosine_similarity(recipe_ingredient_matrix.T)
    
    print("步骤 3/3: 整理结果...")
    # 将numpy数组转换回带有食材名称索引的DataFrame
    classic_similarity_df = pd.DataFrame(
        cosine_sim_matrix,
        index=all_ingredient_names,
        columns=all_ingredient_names
    )
    
    print("--- 共现相似度矩阵计算完成! ---")
    return classic_similarity_df
