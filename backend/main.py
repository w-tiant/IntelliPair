
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.lifespan import lifespan
from src.api import users, recommend, creative, recipes

# FastAPI 实例
app = FastAPI(
    title="智能美食搭配API (重构版)",
    version="9.0.0",
    lifespan=lifespan
)

# CORS 中间件
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由模块
print("正在加载API路由...")
app.include_router(users.router)
app.include_router(recommend.router)
app.include_router(creative.router)
app.include_router(recipes.router)
print("所有API路由加载完毕。")

# 根路径用于测试
@app.get("/")
def read_root():
    return {"message": "欢迎使用美食搭配API (重构版)"}