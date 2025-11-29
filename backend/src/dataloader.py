import pandas as pd
from pathlib import Path
from collections import defaultdict
from pathlib import Path
import json

def load_ingredient_data(data_path: Path):
    """
    加载食材和风味化合物相关的数据。
    """
    print("开始加载食材与风味化合物数据...")
    ingr_comp_path = data_path / "ingr_comp"

    # 1. 加载食材信息
    ingr_info_df = pd.read_csv(
        ingr_comp_path / "ingr_info.tsv", 
        sep='\t', 
        header=None, 
        names=['id', 'name', 'category'],
        skiprows=1  # 跳过第一行
    )
    ingr_info_df['id'] = pd.to_numeric(ingr_info_df['id'])


    # 2. 加载风味化合物信息
    comp_info_df = pd.read_csv(
        ingr_comp_path / "comp_info.tsv",
        sep='\t',
        header=None,
        names=['id', 'name', 'cas', 'pubchem'],
        skiprows=1
    )
    comp_info_df['id'] = pd.to_numeric(comp_info_df['id'])

    # 3. 加载食材-风味化合物关系
    ingr_comp_df = pd.read_csv(
        ingr_comp_path / "ingr_comp.tsv",
        sep='\t',
        header=None,
        names=['ingr_id', 'comp_id'],
        skiprows=1
    )
    ingr_comp_df['ingr_id'] = pd.to_numeric(ingr_comp_df['ingr_id'])
    ingr_comp_df['comp_id'] = pd.to_numeric(ingr_comp_df['comp_id'])
    
    ingr_comp_dict = defaultdict(set)
    for index, row in ingr_comp_df.iterrows():
        ingr_comp_dict[row['ingr_id']].add(row['comp_id'])
        
    print(f"加载完成: {len(ingr_info_df)} 种食材, {len(comp_info_df)} 种风味化合物。")
    return ingr_info_df, comp_info_df, ingr_comp_dict


def load_recipes_data(data_path: Path, ingr_info_df: pd.DataFrame):
    """
    加载所有食谱数据，并将其转换为包含食材标准名称集合的列表。

    Args:
        data_path (Path): 指向 flavor_network_data 目录的路径对象。
        ingr_info_df (pd.DataFrame): 从 load_ingredient_data 加载的食材信息DataFrame。

    Returns:
        List[Set[str]]: 一个食谱列表，其中每个食谱是一个包含食材标准名称的集合。
    """
    print("开始加载食谱数据...")
    recipes_path = data_path / "scirep-cuisines-detail"
    
    # 查找字典
    # name_to_id: 用于将在文件中找到的、带空格的食材名映射到ID
    name_to_id = {
        name.replace('_', ' '): ing_id 
        for ing_id, name in zip(ingr_info_df['id'], ingr_info_df['name'])
    }
    id_to_name = pd.Series(ingr_info_df.name.values, index=ingr_info_df.id).to_dict()
    
    recipe_files = ['allr_recipes.txt', 'epic_recipes.txt', 'menu_recipes.txt']
    # 最终结果是一个列表
    recipes_list_of_sets = []
    
    for file_name in recipe_files:
        print(f"正在处理文件: {file_name}")
        try:
            with open(recipes_path / file_name, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    
                    if len(parts) < 2:
                        continue

                    ingredient_names_from_file = parts[1:]
                    current_recipe_as_names = set()
                    
                    for name in ingredient_names_from_file:
                        ingr_id = name_to_id.get(name)
                        if ingr_id is not None:
                            # 查找ID对应的标准名称
                            canonical_name = id_to_name.get(ingr_id)
                            if canonical_name:
                                current_recipe_as_names.add(canonical_name)
                    
                    # 只有当食谱中至少有一个可识别的食材时，才将其添加到最终列表中
                    if current_recipe_as_names:
                        recipes_list_of_sets.append(current_recipe_as_names)

        except Exception as e:
            print(f"读取文件 {file_name} 时发生严重错误: {e}")

    print(f"加载完成: {len(recipes_list_of_sets)} 份食谱。")
    
    return recipes_list_of_sets

def load_translation_data(i18n_path: Path):
    """加载翻译和别名数据。"""
    print("加载翻译词典...")
    translation_file = i18n_path / "translation.json"
    
    with open(translation_file, 'r', encoding='utf-8') as f:
        translation_data = json.load(f)
    
    alias_to_canonical = {}
    canonical_to_zh = {}
    canonical_to_base = {}

    for canonical_name, data in translation_data.items():
        canonical_to_zh[canonical_name] = data['zh_name']
        
        base_ingredient = data.get('base_ingredient', canonical_name)
        canonical_to_base[canonical_name] = base_ingredient
        
        for alias in data['aliases']:
            alias_to_canonical[alias.lower()] = canonical_name
            
    print(f"翻译词典加载完成...")
    return alias_to_canonical, canonical_to_zh, canonical_to_base