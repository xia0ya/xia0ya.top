"""FastAPI应用入口"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from web.routes import auth, dashboard, reviews, analytics, export, help, users, return_analysis
from web.settings import SECRET_KEY

from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Amazon评论爬虫")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 静态文件
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# 模板
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 注册路由
app.include_router(auth.router, prefix="", tags=["认证"])
app.include_router(dashboard.router, prefix="", tags=["首页"])
app.include_router(reviews.router, prefix="", tags=["评论"])
app.include_router(analytics.router, prefix="", tags=["分析"])
app.include_router(export.router, prefix="", tags=["导出"])
app.include_router(help.router, prefix="", tags=["帮助"])
app.include_router(users.router, prefix="", tags=["用户"])
app.include_router(return_analysis.router, prefix="", tags=["退货分析"])

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

# CORS中间件
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
