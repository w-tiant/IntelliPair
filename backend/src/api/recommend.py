
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from collections import Counter
from itertools import combinations
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from ..core.dependencies import get_db, get_app_data
from ..services import helpers
from ..database.models import User, Preference, LikedCombination

# 路由实例
router = APIRouter(
    prefix="/api",
    tags=["Recommendation Engine"]
)

@router.get("/search-suggestions")
def get_search_suggestions(q: str, app_data: dict = Depends(get_app_data)):
    if not q:
        return {"suggestions": []}
    from rapidfuzz import process, fuzz
    query = q.lower()
    suggestions = process.extract(query, app_data['search_list_zh'], scorer=fuzz.WRatio, limit=5)
    return {"suggestions": [s[0] for s in suggestions]}


@router.get("/recommend")
def get_recommendations(
    mode: str,
    ingredients: str,
    exclude: str = "",
    top_n: int = 10,
    username: str = None,
    db: Session = Depends(get_db),
    app_data: dict = Depends(get_app_data)
):
    input_strings = [s.strip().lower() for s in re.split('[,，]', ingredients) if s.strip()]
    if not input_strings:
        raise HTTPException(status_code=400, detail="未提供任何有效的食材。")

    anchor_ingredients_innovative = []
    translated_anchors_zh = []

    for s in input_strings:
        try:
            _, canonical_name = helpers.get_vector_by_name(s, app_data)
            if canonical_name not in anchor_ingredients_innovative:
                anchor_ingredients_innovative.append(canonical_name)
            zh_name = app_data['canonical_to_zh_map'].get(canonical_name, canonical_name)
            if zh_name not in translated_anchors_zh:
                translated_anchors_zh.append(zh_name)
        except HTTPException as e:
            raise HTTPException(status_code=404, detail=e.detail)

    anchor_ingredients_classic = list(dict.fromkeys(
        app_data['canonical_to_base_map'].get(c, c) for c in anchor_ingredients_innovative
    ))
    
    excluded_strings = [s.strip().lower() for s in re.split('[,，]', exclude) if s.strip()]
    excluded_canonicals_set = set()
    for s in excluded_strings:
        try:
            _, canonical_name = helpers.get_vector_by_name(s, app_data)
            excluded_canonicals_set.add(canonical_name)
        except HTTPException:
            print(f"警告: 无法识别要排除的食材 '{s}'，已跳过。")
            pass

    recommendations_en = []
    
    if mode == 'classic':
        anchor_canonicals_set = set(anchor_ingredients_classic)
        matching_recipes = [
            recipe for recipe in app_data['recipes']
            if (isinstance(recipe, (set, list)) and
                anchor_canonicals_set.issubset(recipe) and
                not excluded_canonicals_set.intersection(recipe))
        ]

        scored_combinations = []
        for recipe_set in matching_recipes:
            if len(recipe_set) > 10 or len(recipe_set) <= len(anchor_canonicals_set):
                continue
            
            total_score, pair_count = 0, 0
            for ingr1, ingr2 in combinations(recipe_set, 2):
                if ingr1 in app_data['classic_sim_df'].index and ingr2 in app_data['classic_sim_df'].index:
                    try:
                        score = app_data['classic_sim_df'].loc[ingr1, ingr2]
                        total_score += score
                        pair_count += 1
                    except KeyError:
                        continue
            
            average_score = total_score / pair_count if pair_count > 0 else 0
            if average_score > 0:
                scored_combinations.append({
                    "combination": list(recipe_set),
                    "score": average_score
                })

        sorted_combinations = sorted(scored_combinations, key=lambda x: x['score'], reverse=True)
        
        unique_combinations = []
        seen_sets = set()
        for item in sorted_combinations:
            combination_frozenset = frozenset(item['combination'])
            if combination_frozenset not in seen_sets:
                unique_combinations.append(item)
                seen_sets.add(combination_frozenset)
        
        recommendations_en = unique_combinations[:top_n]
    
    elif mode == 'innovative':
        flavor_scores = app_data['innovative_sim_df'].loc[anchor_ingredients_innovative].sum()
        multimodal_scores = app_data['multimodal_sim_df'].loc[anchor_ingredients_innovative].sum()
        combined_scores = 0.6 * flavor_scores + 0.4 * multimodal_scores
        
        if username:
            taste_vector = helpers.get_user_taste_vector(username, db, app_data)
            if taste_vector is not None:
                # ... (个性化逻辑不变)
                taste_similarity = cosine_similarity([taste_vector], app_data['aligned_embeddings'])[0]
                taste_scores = pd.Series(taste_similarity, index=app_data['name_to_idx_map'].keys())
                personalization_weight = 0.35
                combined_scores = (1 - personalization_weight) * combined_scores + personalization_weight * taste_scores

        anchor_categories = {app_data['ingr_to_category_map'].get(ingr) for ingr in anchor_ingredients_innovative}
        combined_scores.drop(anchor_ingredients_innovative, inplace=True, errors='ignore')
        if excluded_canonicals_set:
            combined_scores.drop(labels=excluded_canonicals_set, inplace=True, errors='ignore')
        
        valid_candidates = [
            name for name in combined_scores.index 
            if app_data['ingr_to_category_map'].get(name) not in anchor_categories
        ]
        top_results = combined_scores.loc[valid_candidates].nlargest(top_n)
        recommendations_en = [{"ingredient": name, "score": score} for name, score in top_results.items()]
    
    else:
        raise HTTPException(status_code=400, detail="模式无效。")

    if mode == 'classic':
        recommendations_zh = [
            {
                "combination": [app_data['canonical_to_zh_map'].get(ingr, ingr) for ingr in item["combination"]],
                "score": item["score"]
            }
            for item in recommendations_en
        ]
        for i, item in enumerate(recommendations_en):
            recommendations_zh[i]['combination_en'] = item['combination']
    else:
        recommendations_zh = [{"ingredient": app_data['canonical_to_zh_map'].get(item["ingredient"], item["ingredient"]), "score": item["score"]} for item in recommendations_en]

    # 用户偏好
    user_preferences = set()
    liked_combo_signatures = []
    if username:
        user = db.query(User).filter(User.username == username).first()
        if user:
            prefs_query = db.query(Preference.ingredient_name).filter(
                Preference.user_id == user.id, Preference.liked == True
            ).all()
            # 将 [(name1,), (name2,)] 的形式转换为 {'name1', 'name2'} 集合，便于前端快速查找
            user_preferences = {item[0] for item in prefs_query}
            combo_sigs_query = db.query(LikedCombination.signature).filter(LikedCombination.user_id == user.id).all()
            liked_combo_signatures = [item[0] for item in combo_sigs_query]

    return {
        "anchor_ingredients": translated_anchors_zh, 
        "recommendations": recommendations_zh,
        "liked_ingredients": list(user_preferences),
        "liked_combinations": liked_combo_signatures
    }
    

@router.get("/generate-idea")
def generate_recipe_idea(
    ingredients: str,
    exclude: str = "",
    top_n_complements: int = 5,
    app_data: dict = Depends(get_app_data)
):
    core_canonicals = set()
    core_zh = set()
    input_strings = [s.strip().lower() for s in re.split('[,，]', ingredients) if s.strip()]
    
    if len(input_strings) < 2:
        raise HTTPException(status_code=400, detail="请至少输入两种核心食材。")

    for s in input_strings:
        try:
            _, canonical_name = helpers.get_vector_by_name(s, app_data)
            core_canonicals.add(canonical_name)
            core_zh.add(app_data['canonical_to_zh_map'].get(canonical_name, canonical_name))
        except HTTPException as e:
            raise HTTPException(status_code=404, detail=e.detail)
    
    excluded_strings = [s.strip().lower() for s in re.split('[,，]', exclude) if s.strip()]
    excluded_canonicals_set = set()
    for s in excluded_strings:
        try:
            _, canonical_name = helpers.get_vector_by_name(s, app_data)
            excluded_canonicals_set.add(canonical_name)
        except HTTPException:
            print(f"警告 (菜谱灵感): 无法识别要排除的食材 '{s}'，已跳过。")
            pass

    anchor1, anchor2 = list(core_canonicals)[:2]
    anchor1_zh, anchor2_zh = list(core_zh)[:2]

    classic_score = app_data['classic_sim_df'].loc[anchor1, anchor2] if anchor1 in app_data['classic_sim_df'].index and anchor2 in app_data['classic_sim_df'].columns else 0
    innovative_score = app_data['innovative_sim_df'].loc[anchor1, anchor2] if anchor1 in app_data['innovative_sim_df'].index and anchor2 in app_data['innovative_sim_df'].columns else 0

    pairing_story = f" {anchor1_zh} 和 {anchor2_zh} "
    if classic_score > 0.1:
        pairing_story += f"是一对经过时间考验的经典搭档，在无数传统菜肴中都能看到它们的身影，风味高度协同。"
    elif innovative_score > 0.2:
        pairing_story += f"共享着一些关键的风味化合物，这使得它们的搭配能在味觉上产生意想不到的和谐共鸣。"
    else:
        pairing_story += f"的搭配可能会在质地、营养或功能上形成有趣的互补，值得进行一次美食冒险。"

    matching_recipes = [
        recipe for recipe in app_data['recipes'] 
        if core_canonicals.issubset(recipe)
    ]

    complements = []
    if not matching_recipes:
        pairing_story += " 在我们的数据中，这是一个非常罕见的组合，因此暂时无法推荐更多互补食材。"
    else:
        complement_counter = Counter()
        for recipe in matching_recipes:
            complement_counter.update(recipe - core_canonicals)
        
        all_possible_complements = complement_counter.most_common()
        filtered_complements = [
            (name, count) for name, count in all_possible_complements
            if name not in excluded_canonicals_set
        ]
        top_complements_en = filtered_complements[:top_n_complements]
        complements = [
            app_data['canonical_to_zh_map'].get(name, name) for name, count in top_complements_en
        ]

    return {
        "core_ingredients": list(core_zh),
        "pairing_story": pairing_story,
        "complementary_ingredients": complements
    }