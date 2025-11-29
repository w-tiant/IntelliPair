
import httpx
import asyncio
import random
import urllib.parse
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from parsel import Selector
from typing import List
from pydantic import BaseModel

class RecipeLink(BaseModel):
    title: str
    url: str 
    source: str

router = APIRouter(
    prefix="/api",
    tags=["Recipes"]
)

def get_source_from_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    
    # 常见菜谱网站映射
    if "douguo.com" in domain: return "豆果美食"
    if "meishijie.cc" in domain: return "美食杰"
    if "meishichina.com" in domain: return "美食天下"
    if "xiachufang.com" in domain: return "下厨房"
    if "bilibili.com" in domain: return "Bilibili"
    if "zhihu.com" in domain: return "知乎"
    if "youtube.com" in domain: return "YouTube"
    if "hongchufu.com" in domain: return "红厨网"
    if "xiangha.com" in domain: return "香哈菜谱"
    if "baidu.com" in domain: return "百度经验"
    
    # 如果都不匹配，返回域名本身 (去掉 www.)
    return domain.replace("www.", "")

# --- 1. 下厨房直连 ---
async def search_xiachufang(client, query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.xiachufang.com/search/?keyword={encoded_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        response = await client.get(url, headers=headers, follow_redirects=True)
        selector = Selector(text=response.text)
        results = []
        links = selector.css(".normal-recipe-list .recipe .info .name a")
        for link in links[:6]: 
            title = link.xpath("string(.)").get("").strip()
            href = link.css("::attr(href)").get()
            if title and href:
                results.append(RecipeLink(
                    title=title, 
                    url=f"https://www.xiachufang.com{href}",
                    source="下厨房"
                ))
        print(f"[Crawler] 下厨房 (Direct) found: {len(results)}")
        return results
    except Exception as e:
        print(f"[Crawler] Xiachufang Error: {e}")
        return []

# --- 2. Bing 通用聚合搜索 ---
async def search_bing_general(client, query):
    search_query = f"{query} 做法" 
    encoded_query = urllib.parse.quote(search_query)
    
    url = f"https://cn.bing.com/search?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    try:
        response = await client.get(url, headers=headers, follow_redirects=True)
        selector = Selector(text=response.text)
        results = []
        
        items = selector.css("li.b_algo")
        
        for item in items[:10]:
            link_node = item.css("h2 a")
            title = link_node.xpath("string(.)").get("").strip()
            href = link_node.css("::attr(href)").get()
            
            if title and href and href.startswith("http"):
                
                if "xiachufang.com" in href:
                    continue
                
                if "bing.com" in href or "microsoft.com" in href:
                    continue

                clean_title = title.split(" - ")[0].split("_")[0].split("|")[0]
                
                source_name = get_source_from_url(href)
                results.append(RecipeLink(
                    title=clean_title, 
                    url=href,
                    source=source_name
                ))
        
        print(f"[Crawler] Bing (General) found: {len(results)}")
        return results

    except Exception as e:
        print(f"[Crawler] Bing General Error: {e}")
        return []

# --- API 端点 ---

@router.get("/find-recipes", response_model=List[RecipeLink])
async def find_recipes(ingredients: List[str] = Query(..., description="要搜索的食材列表")):
    if not ingredients:
        raise HTTPException(status_code=400, detail="食材列表不能为空。")

    query = " ".join(ingredients)
    print(f"\n--- Starting General Search for: {query} ---")

    async with httpx.AsyncClient(timeout=15.0) as client:
        tasks = [
            search_xiachufang(client, query),
            search_bing_general(client, query)
        ]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

    final_recipes = []
    for res in results_list:
        if isinstance(res, list):
            final_recipes.extend(res)
        else:
            print(f"[System] Task failed: {res}")
    
    # 去重
    seen_urls = set()
    unique_recipes = []
    
    for r in final_recipes:
        normalized = r.url.rstrip("/")
        if normalized not in seen_urls:
            unique_recipes.append(r)
            seen_urls.add(normalized)

    random.shuffle(unique_recipes)
    
    print(f"--- Final Results: {len(unique_recipes)} ---\n")
    return unique_recipes