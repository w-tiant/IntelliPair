
import re
import json
import numpy as np
import pandas as pd
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sklearn.metrics.pairwise import cosine_similarity

from ..core.dependencies import get_app_data
from ..services import helpers
from ..schemas.main_schemas import CombinationPayload

# 创建路由实例
router = APIRouter(
    prefix="/api",
    tags=["Creative Tools"]
)


@router.get("/alchemy")
def perform_alchemy(
    base: str,
    add: str = "",
    subtract: str = "",
    top_n: int = 10,
    app_data: dict = Depends(get_app_data)
):
    base_ingredient_input = base.strip().lower()
    if not base_ingredient_input:
        raise HTTPException(status_code=400, detail="必须提供基础食材。")

    add_ingredients_input = [s.strip().lower() for s in re.split('[,，]', add) if s.strip()]
    subtract_ingredients_input = [s.strip().lower() for s in re.split('[,，]', subtract) if s.strip()]

    try:
        target_vec, base_canonical = helpers.get_vector_by_name(base_ingredient_input, app_data)
        target_vec = target_vec.copy()

        added_canonicals = [helpers.get_vector_by_name(ingr, app_data)[1] for ingr in add_ingredients_input]
        subtracted_canonicals = [helpers.get_vector_by_name(ingr, app_data)[1] for ingr in subtract_ingredients_input]

        for ingr in add_ingredients_input:
            target_vec += helpers.get_vector_by_name(ingr, app_data)[0]
        for ingr in subtract_ingredients_input:
            target_vec -= helpers.get_vector_by_name(ingr, app_data)[0]
    except HTTPException as e:
        raise HTTPException(status_code=404, detail=e.detail)

    similarities = cosine_similarity([target_vec], app_data['aligned_embeddings'])[0]
    sim_series = pd.Series(similarities, index=app_data['name_to_idx_map'].keys())

    exclude_ingredients = {base_canonical} | set(added_canonicals) | set(subtracted_canonicals)
    sim_series.drop(labels=exclude_ingredients, inplace=True, errors='ignore')

    top_results = sim_series.nlargest(top_n)

    recommendations_zh = [{"ingredient": app_data['canonical_to_zh_map'].get(name, name), "score": score} for name, score in top_results.items()]
    operation_details = {
        "base": app_data['canonical_to_zh_map'].get(base_canonical, base_canonical),
        "add": [app_data['canonical_to_zh_map'].get(c, c) for c in added_canonicals],
        "subtract": [app_data['canonical_to_zh_map'].get(c, c) for c in subtracted_canonicals]
    }
    return {"operation": operation_details, "recommendations": recommendations_zh}


@router.get("/find-bridge")
def find_bridge_ingredients(
    start: str,
    end: str,
    steps: int = 1,
    app_data: dict = Depends(get_app_data)
):
    if not start or not end:
        raise HTTPException(status_code=400, detail="必须提供起点和终点食材。")
    if not 1 <= steps <= 3:
        raise HTTPException(status_code=400, detail="桥梁数量必须在1到3之间。")

    try:
        start_vec, start_canonical = helpers.get_vector_by_name(start, app_data)
        end_vec, end_canonical = helpers.get_vector_by_name(end, app_data)
    except HTTPException as e:
        raise HTTPException(status_code=404, detail=e.detail)

    def find_creative_pivot(vec1, canon1, vec2, canon2, exclude_canonicals, creativity_factor=1.5):
        cat1 = app_data['ingr_to_category_map'].get(canon1)
        cat2 = app_data['ingr_to_category_map'].get(canon2)
        
        sim_to_vec1 = cosine_similarity([vec1], app_data['aligned_embeddings'])[0]
        sim_to_vec2 = cosine_similarity([vec2], app_data['aligned_embeddings'])[0]
        sim_to_vec1[sim_to_vec1 < 0] = 0
        sim_to_vec2[sim_to_vec2 < 0] = 0
        
        pivot_scores = sim_to_vec1 * sim_to_vec2
        bonus = np.ones_like(pivot_scores)
        for i, name in enumerate(app_data['idx_to_name_map'].values()):
            candidate_cat = app_data['ingr_to_category_map'].get(name)
            if candidate_cat not in [cat1, cat2]:
                bonus[i] = creativity_factor
        
        creative_scores = pivot_scores * bonus
        exclude_indices = [app_data['name_to_idx_map'][name] for name in exclude_canonicals if name in app_data['name_to_idx_map']]
        
        creative_scores[exclude_indices] = -1
        best_pivot_idx = np.argmax(creative_scores)
        return app_data['idx_to_name_map'][best_pivot_idx]

    path_en = [start_canonical]
    current_vec, current_canonical = start_vec, start_canonical
    for _ in range(steps):
        exclude_set = set(path_en) | {end_canonical}
        pivot = find_creative_pivot(current_vec, current_canonical, end_vec, end_canonical, exclude_set)
        path_en.append(pivot)
        current_vec, current_canonical = helpers.get_vector_by_name(pivot, app_data)

    path_en.append(end_canonical)
    unique_path_en = list(dict.fromkeys(path_en))
    path_zh = [app_data['canonical_to_zh_map'].get(name, name) for name in unique_path_en]
    return {"path": path_zh}


@router.post("/generate-concept")
def generate_concept_api(payload: CombinationPayload):
    ingredients = payload.combination
    if not ingredients or len(ingredients) < 2:
        raise HTTPException(status_code=400, detail="请至少提供两种食材来生成概念。")

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        你是一位富有创意的顶级大厨。请为以下食材组合设计一个菜谱概念。
        食材: {', '.join(ingredients)}

        请严格按照以下JSON格式返回，不要包含任何markdown标记 (例如 ```json) 或其他解释性文字，只返回纯粹的JSON对象：
        {{
          "dish_name": "一个富有创意的菜名",
          "description": "一句引人入胜的描述，说明这些食材如何协同工作，不超过100字",
          "key_steps": ["关键步骤1", "关键步骤2", "关键步骤3"],
          "flavor_profile": "总结这道菜的风味亮点，用3-4个词，以逗号分隔"
        }}
        """
        response = model.generate_content(prompt)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        concept_data = json.loads(cleaned_response_text)
        return concept_data
    except json.JSONDecodeError:
        print(f"Gemini API返回了非JSON格式的内容: {response.text}")
        raise HTTPException(status_code=500, detail="AI服务返回格式错误，请稍后再试。")
    except Exception as e:
        print(f"调用Gemini API时出错: {e}")
        raise HTTPException(status_code=500, detail="无法连接AI服务，请稍后再试。")
    