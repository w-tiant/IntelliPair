import pandas as pd
from typing import List, Dict

def recommend(similarity_df: pd.DataFrame, anchor_ingredients: List[str], top_n: int) -> List[dict]:
    """
    通用的推荐函数，根据给定的相似度矩阵进行推荐。
    """
    valid_anchors = [ingr for ingr in anchor_ingredients if ingr in similarity_df.index]
    if not valid_anchors:
        return []

    combined_scores = similarity_df.loc[valid_anchors].sum(axis=0)
    combined_scores = combined_scores.drop(labels=valid_anchors, errors='ignore')
    top_recommendations = combined_scores.nlargest(top_n)
    
    result = [
        {"ingredient": name, "score": score} 
        for name, score in top_recommendations.items()
    ]
    return result

def recommend_classic(similarity_df: pd.DataFrame, anchor_ingredients: List[str], top_n: int) -> List[dict]:
    return recommend(similarity_df, anchor_ingredients, top_n)

def recommend_innovative_filtered(
    similarity_df: pd.DataFrame, 
    anchor_ingredients: List[str], 
    top_n: int, 
    category_map: Dict[str, str]
) -> List[dict]:
    """
    在创新推荐中，过滤掉与锚点食材同类的结果。
    """
    anchor_categories = {category_map.get(ingr) for ingr in anchor_ingredients if ingr in category_map}
    
    initial_pool_size = top_n * 10 # 增加初始池的大小，因为很多会被过滤掉
    initial_recommendations = recommend(similarity_df, anchor_ingredients, initial_pool_size)
    
    filtered_recommendations = []
    for item in initial_recommendations:
        if len(filtered_recommendations) >= top_n:
            break
            
        candidate_name = item['ingredient']
        candidate_category = category_map.get(candidate_name)
        
        # 候选者的类别必须存在 (不为None)，并且不能与锚点食材的类别相同。
        if candidate_category is not None and candidate_category not in anchor_categories:
            filtered_recommendations.append(item)
            
    return filtered_recommendations

def recommend_innovative(similarity_df: pd.DataFrame, anchor_ingredients: List[str], top_n: int, category_map: Dict[str, str]) -> List[dict]:
    return recommend_innovative_filtered(similarity_df, anchor_ingredients, top_n, category_map)