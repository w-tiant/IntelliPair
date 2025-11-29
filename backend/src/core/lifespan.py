
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
import pandas as pd
import numpy as np
import os
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity

from ..database.database import create_db_and_tables
from ..dataloader import load_ingredient_data, load_recipes_data, load_translation_data
from ..similarity_engine import calculate_cooccurrence_similarity, calculate_flavor_similarity

app_data = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's startup and shutdown events.
    """
    print("--- Server Starting Up ---")
    
    create_db_and_tables()

    # --- API Key ---
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("Please set the GOOGLE_API_KEY environment variable")
    genai.configure(api_key=GOOGLE_API_KEY)

    # --- 路径 ---
    DATA_DIR = Path("./data/flavor_network_data")
    I18N_DIR = Path("./i18n")
    CACHE_DIR = Path("./cache")
    CACHE_DIR.mkdir(exist_ok=True)
    CLASSIC_SIM_CACHE_PATH = CACHE_DIR / "classic_similarity.feather"
    INNOVATIVE_SIM_CACHE_PATH = CACHE_DIR / "innovative_similarity.feather"
    MULTIMODAL_SIM_CACHE_PATH = CACHE_DIR / "multimodal_similarity.feather"
    ALIGNED_EMB_PATH = Path("./data/aligned_multimodal_embeddings.npy")

    ingr_info, _, ingr_comp = load_ingredient_data(DATA_DIR)
    alias_map, zh_map, base_map = load_translation_data(I18N_DIR)
    
    app_data['ingr_info_df'] = ingr_info
    app_data['alias_to_canonical_map'] = alias_map
    app_data['canonical_to_zh_map'] = zh_map
    app_data['canonical_to_base_map'] = base_map
    app_data['ingr_to_category_map'] = pd.Series(ingr_info.category.values, index=ingr_info.name).to_dict()

    # --- Cache ---
    if os.path.exists(CLASSIC_SIM_CACHE_PATH):
        app_data['classic_sim_df'] = pd.read_feather(CLASSIC_SIM_CACHE_PATH).set_index('index')
    else:
        recipes = load_recipes_data(DATA_DIR, ingr_info)
        classic_sim_df = calculate_cooccurrence_similarity(recipes, ingr_info)
        app_data['classic_sim_df'] = classic_sim_df
        classic_sim_df.reset_index().to_feather(CLASSIC_SIM_CACHE_PATH)
    
    # Innovative
    if os.path.exists(INNOVATIVE_SIM_CACHE_PATH):
        app_data['innovative_sim_df'] = pd.read_feather(INNOVATIVE_SIM_CACHE_PATH).set_index('index')
    else:
        innovative_sim_df = calculate_flavor_similarity(ingr_comp, ingr_info)
        app_data['innovative_sim_df'] = innovative_sim_df
        innovative_sim_df.reset_index().to_feather(INNOVATIVE_SIM_CACHE_PATH)
        
    # Multimodal
    if os.path.exists(MULTIMODAL_SIM_CACHE_PATH):
        app_data['multimodal_sim_df'] = pd.read_feather(MULTIMODAL_SIM_CACHE_PATH).set_index('index')
    else:
        aligned_embeddings = np.load(ALIGNED_EMB_PATH)
        multimodal_sim_matrix = cosine_similarity(aligned_embeddings)
        ingr_info_df_sorted = app_data['ingr_info_df'].copy().sort_values('id')
        target_names = ingr_info_df_sorted['name'].tolist()
        multimodal_sim_df = pd.DataFrame(multimodal_sim_matrix, index=target_names, columns=target_names)
        app_data['multimodal_sim_df'] = multimodal_sim_df
        multimodal_sim_df.reset_index().to_feather(MULTIMODAL_SIM_CACHE_PATH)

    app_data['aligned_embeddings'] = np.load(ALIGNED_EMB_PATH)
    ingr_info_df_sorted = app_data['ingr_info_df'].copy().sort_values('id')
    app_data['name_to_idx_map'] = {name: i for i, name in enumerate(ingr_info_df_sorted['name'])}
    app_data['idx_to_name_map'] = {i: name for i, name in enumerate(ingr_info_df_sorted['name'])}
    
    app_data['ingredient_name_list'] = list(app_data['name_to_idx_map'].keys())
    app_data['search_list_zh'] = list(app_data['canonical_to_zh_map'].values())
    app_data['zh_to_canonical_map'] = {v: k for k, v in app_data['canonical_to_zh_map'].items()}
    
    app_data['recipes'] = load_recipes_data(DATA_DIR, app_data['ingr_info_df'])

    print("--- Server is Ready! ---")
    
    yield
    
    print("--- Server Shutting Down ---")
    app_data.clear()