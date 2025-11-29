
import pandas as pd
import json
from pathlib import Path
from deep_translator import GoogleTranslator
from tqdm import tqdm
import time

# --- 配置 ---
I18N_DIR = Path("./i18n")
DATA_DIR = Path("./data/flavor_network_data")
INPUT_TRANSLATION_FILE = I18N_DIR / "translation.json"
OUTPUT_TRANSLATION_FILE = I18N_DIR / "translation_new.json"
INGREDIENT_INFO_FILE = DATA_DIR / "ingr_comp" / "ingr_info.tsv"

def run_translator():
    print("--- 开始自动化翻译流程 ---")

    # 1. 官方食材信息
    print("加载官方食材列表...")
    ingr_info_df = pd.read_csv(
        INGREDIENT_INFO_FILE, 
        sep='\t', 
        header=None, 
        names=['id', 'name', 'category'],
        skiprows=1
    )
    all_ingredients = ingr_info_df['name'].tolist()
    print(f"共找到 {len(all_ingredients)} 种官方食材。")

    # 2. 加载已有的手动翻译
    if INPUT_TRANSLATION_FILE.exists():
        print(f"加载已有的手动翻译文件: {INPUT_TRANSLATION_FILE}")
        with open(INPUT_TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            existing_translations = json.load(f)
    else:
        existing_translations = {}
    print(f"已有 {len(existing_translations)} 条手动翻译。")

    # 3. 新食材
    new_ingredients_to_translate = [
        name for name in all_ingredients if name not in existing_translations
    ]
    if not new_ingredients_to_translate:
        print("所有食材都已翻译，无需操作。")
        return

    print(f"发现 {len(new_ingredients_to_translate)} 种新食材需要翻译。")

    # 4. 翻译
    translator = GoogleTranslator(source='en', target='zh-CN')
    
    final_translations = existing_translations.copy()
    for name in tqdm(new_ingredients_to_translate, desc="正在翻译"):
        try:
            # 将下划线替换为空格再翻译
            clean_name = name.replace('_', ' ')
            translated_text = translator.translate(clean_name)
            
            # 创建新的词典条目
            final_translations[name] = {
                "zh_name": translated_text,
                "aliases": [name, translated_text] # 添加英文和中文作为别名
            }
            # 延迟，避免因请求过快被API封禁
            time.sleep(0.1) 

        except Exception as e:
            print(f"\n翻译 '{name}' 时发生错误: {e}")
            # 出错，创建一个基础条目，方便后续手动修改
            final_translations[name] = {
                "zh_name": name, # 翻译失败，用英文名代替
                "aliases": [name]
            }

    # 5. 保存翻译文件
    print(f"\n翻译完成！总共 {len(final_translations)} 条翻译。")
    print(f"正在保存到新文件: {OUTPUT_TRANSLATION_FILE}")
    with open(OUTPUT_TRANSLATION_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False 确保中文字符ok
        json.dump(final_translations, f, ensure_ascii=False, indent=2)

    print("--- 流程结束 ---")

if __name__ == "__main__":
    run_translator()