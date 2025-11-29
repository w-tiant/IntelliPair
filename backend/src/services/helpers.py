
import numpy as np
from rapidfuzz import process, fuzz
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Tuple, Union

from ..database.models import User, Preference, LikedCombination


def get_vector_by_name(name: str, app_data: dict) -> Tuple[np.ndarray, str]:
    """
    通过名称获取食材的向量和规范名称。
    """
    name = name.strip().lower()
    
    canonical_name = app_data['alias_to_canonical_map'].get(name, name)
    
    # 直接匹配规范名称
    if canonical_name in app_data['name_to_idx_map']:
        idx = app_data['name_to_idx_map'][canonical_name]
        return app_data['aligned_embeddings'][idx], canonical_name
    
    # 尝试模糊匹配中文名
    zh_match = process.extractOne(name, app_data['search_list_zh'], scorer=fuzz.WRatio, score_cutoff=85)
    if zh_match:
        matched_zh = zh_match[0]
        canonical_name = app_data['zh_to_canonical_map'][matched_zh]
        print(f"模糊匹配(中文)成功: '{name}' -> '{matched_zh}' ({canonical_name})")
        idx = app_data['name_to_idx_map'][canonical_name]
        return app_data['aligned_embeddings'][idx], canonical_name
        
    # 尝试模糊匹配英文规范名
    en_match = process.extractOne(name, app_data['ingredient_name_list'], scorer=fuzz.WRatio, score_cutoff=85)
    if en_match:
        matched_en = en_match[0]
        print(f"模糊匹配(英文)成功: '{name}' -> '{matched_en}'")
        idx = app_data['name_to_idx_map'][matched_en]
        return app_data['aligned_embeddings'][idx], matched_en

    print(f"匹配失败: 无法为 '{name}' 找到任何相似食材。")
    raise HTTPException(status_code=404, detail=f"食材 '{name}' 无法识别，也找不到相似的选项。")


def get_user_taste_vector(username: str, db: Session, app_data: dict) -> Union[np.ndarray, None]:
    """
    计算用户的平均口味向量
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None

    all_taste_vectors = []

    # 1. 从单个点赞的食材中获取向量
    liked_prefs = db.query(Preference.ingredient_name).filter(Preference.user_id == user.id).all()
    for pref in liked_prefs:
        ingr_name = pref[0]
        if ingr_name in app_data['name_to_idx_map']:
            idx = app_data['name_to_idx_map'][ingr_name]
            all_taste_vectors.append(app_data['aligned_embeddings'][idx])

    # 2. 从点赞的组合中获取向量
    liked_combos = db.query(LikedCombination).filter(LikedCombination.user_id == user.id).all()
    for combo in liked_combos:
        combo_vectors = []
        for combo_ingr in combo.ingredients:
            ingr_name = combo_ingr.ingredient_name
            if ingr_name in app_data['name_to_idx_map']:
                idx = app_data['name_to_idx_map'][ingr_name]
                combo_vectors.append(app_data['aligned_embeddings'][idx])
        
        if combo_vectors:
            combo_average_vector = np.mean(combo_vectors, axis=0)
            all_taste_vectors.append(combo_average_vector)

    if not all_taste_vectors:
        return None
    
    # 3. 最终平均值
    return np.mean(all_taste_vectors, axis=0)