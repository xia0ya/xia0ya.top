# Amazon 评论爬虫 Web 服务实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为业务人员提供网页界面的Amazon评论爬取和分析工具

**Architecture:** FastAPI后端 + Jinja2模板前端 + SQLite数据库 + Session认证。复用现有爬虫逻辑，通过后台异步任务执行爬取，前端轮询获取状态。

**Tech Stack:** FastAPI, Jinja2, TailwindCSS, SQLite, httpx/sync_playwright

---

## 文件结构

```
web/
├── main.py                    # FastAPI入口
├── config.py                  # Web配置
├── templates/                 # Jinja2模板
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── reviews.html
│   ├── analytics.html
│   └── help.html              # 说明文档页
├── static/
│   └── css/
│       └── custom.css
├── routes/
│   ├── __init__.py
│   ├── auth.py               # 登录/登出
│   ├── dashboard.py          # 主页/任务
│   ├── reviews.py            # 评论列表
│   ├── analytics.py          # 分析页面
│   └── export.py             # 导出
├── services/
│   ├── __init__.py
│   ├── scraper_service.py    # 爬虫任务服务
│   ├── analytics_service.py  # 分析服务
│   └── user_service.py       # 用户服务
├── models/
│   ├── __init__.py
│   └── user.py               # 用户模型
└── utils/
    ├── __init__.py
    └── decorators.py         # 登录校验装饰器
```

---

### Task 1: 项目初始化与配置

**Files:**
- Create: `web/config.py`
- Create: `web/main.py`
- Create: `web/templates/base.html`
- Create: `web/static/css/custom.css`

- [ ] **Step 1: 创建 web/config.py**

```python
"""Web应用配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR.parent / "database" / "products.db"))
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
SESSION_LIFETIME = 3600 * 24  # 24小时

# 爬虫配置
MAX_CONCURRENT_TASKS = 3
TASK_TIMEOUT = 600  # 10分钟

# 分页
PAGE_SIZE = 20
```

- [ ] **Step 2: 创建 web/main.py**

```python
"""FastAPI应用入口"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from routes import auth, dashboard, reviews, analytics, export

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Amazon评论爬虫")

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

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")
```

- [ ] **Step 3: 创建 web/templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Amazon评论爬虫{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/static/css/custom.css">
</head>
<body class="bg-gray-100 min-h-screen">
    {% if current_user %}
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <div class="flex space-x-6">
                <a href="/dashboard" class="nav-link {{ 'active' if request.url.path == '/dashboard' }}">首页</a>
                <a href="/reviews" class="nav-link {{ 'active' if request.url.path == '/reviews' }}">评论列表</a>
                <a href="/analytics" class="nav-link {{ 'active' if request.url.path == '/analytics' }}">数据分析</a>
                <a href="/help" class="nav-link {{ 'active' if request.url.path == '/help' }}">使用说明</a>
            </div>
            <div class="flex items-center space-x-4">
                <span class="text-gray-600">{{ current_user }}</span>
                <a href="/logout" class="text-red-600 hover:underline">登出</a>
            </div>
        </div>
    </nav>
    {% endif %}

    <main class="max-w-7xl mx-auto px-4 py-6">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

- [ ] **Step 4: 创建 web/static/css/custom.css**

```css
.nav-link {
    @apply text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium;
}
.nav-link.active {
    @apply text-blue-600 bg-blue-50;
}
```

- [ ] **Step 5: 创建 web/routes/__init__.py**

```python
"""路由包"""
```

- [ ] **Step 6: 创建 web/services/__init__.py**

```python
"""服务包"""
```

- [ ] **Step 7: 创建 web/models/__init__.py**

```python
"""模型包"""
```

- [ ] **Step 8: 创建 web/utils/__init__.py**

```python
"""工具包"""
```

- [ ] **Step 9: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): initial project structure"
```

---

### Task 2: 用户认证

**Files:**
- Create: `web/models/user.py`
- Create: `web/services/user_service.py`
- Create: `web/routes/auth.py`
- Create: `web/templates/login.html`
- Modify: `web/utils/decorators.py`

- [ ] **Step 1: 创建 web/models/user.py**

```python
"""用户模型"""
import sqlite3
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from web.config import DATABASE_PATH

@dataclass
class User:
    id: int
    username: str
    created_at: str

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed

def init_users_table():
    """初始化用户表"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 创建默认管理员账号 admin/admin123
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  ("admin", hash_password("admin123")))
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> User | None:
    """根据用户名获取用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(id=row["id"], username=row["username"], created_at=row["created_at"])
    return None

def authenticate(username: str, password: str) -> User | None:
    """验证用户登录"""
    user = get_user_by_username(username)
    if user and verify_password(password, get_password_hash(user.id)):
        return user
    return None

def get_password_hash(user_id: int) -> str:
    """获取用户密码哈希"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""
```

- [ ] **Step 2: 创建 web/services/user_service.py**

```python
"""用户服务"""
from models.user import User, authenticate, get_user_by_username, init_users_table

class UserService:
    @staticmethod
    def login(username: str, password: str) -> User | None:
        return authenticate(username, password)

    @staticmethod
    def get_user(username: str) -> User | None:
        return get_user_by_username(username)

    @staticmethod
    def init():
        init_users_table()
```

- [ ] **Step 3: 创建 web/utils/decorators.py**

```python
"""登录校验装饰器"""
from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        username = request.session.get("user")
        if not username:
            return RedirectResponse(url="/login")
        return await func(request, *args, **kwargs)
    return wrapper

def get_current_user(request: Request) -> str | None:
    return request.session.get("user")
```

- [ ] **Step 4: 创建 web/routes/auth.py**

```python
"""认证路由"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from services.user_service import UserService

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/login")
async def login_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = UserService.login(username, password)
    if user:
        request.session["user"] = user.username
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login?error=invalid", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
```

- [ ] **Step 5: 创建 web/templates/login.html**

```html
{% extends "base.html" %}

{% block title %}登录 - Amazon评论爬虫{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-10">
    <div class="bg-white rounded-lg shadow-md p-8">
        <h1 class="text-2xl font-bold mb-6 text-center">Amazon评论爬虫</h1>

        {% if error %}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            用户名或密码错误
        </div>
        {% endif %}

        <form method="post" action="/login">
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="username">
                    用户名
                </label>
                <input type="text" id="username" name="username" required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div class="mb-6">
                <label class="block text-gray-700 text-sm font-bold mb-2" for="password">
                    密码
                </label>
                <input type="password" id="password" name="password" required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button type="submit"
                class="w-full bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700">
                登录
            </button>
        </form>

        <p class="mt-4 text-center text-gray-500 text-sm">
            默认账号: admin / admin123
        </p>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 6: 修改 main.py 添加session中间件**

在 `web/main.py` 的 app = FastAPI() 后添加:
```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
```

- [ ] **Step 7: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): add user authentication"
```

---

### Task 3: Dashboard 页面 - 链接提交与任务列表

**Files:**
- Create: `web/routes/dashboard.py`
- Create: `web/templates/dashboard.html`
- Create: `web/services/scraper_service.py`

- [ ] **Step 1: 创建 web/services/scraper_service.py**

```python
"""爬虫任务服务"""
import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from proxy.manager import ProxyManager, ProxyMode
from scraper.review_page import ReviewPageController
from scraper.review_extractor import ReviewExtractor
from core.link_parser import LinkParser

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ScrapeTask:
    id: str
    asin: str
    original_url: str
    status: TaskStatus = TaskStatus.PENDING
    review_count: int = 0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: Optional[str] = None

class ScraperService:
    _tasks: dict[str, ScrapeTask] = {}
    _lock = threading.Lock()
    _executor_thread: Optional[threading.Thread] = None
    _running = False

    @classmethod
    def add_task(cls, url: str) -> ScrapeTask:
        """添加爬虫任务"""
        asin = LinkParser.extract_asin(url)
        if not asin:
            task = ScrapeTask(
                id=f"task_{datetime.now().timestamp()}",
                asin="",
                original_url=url,
                status=TaskStatus.FAILED,
                error="无法提取ASIN"
            )
        else:
            task = ScrapeTask(
                id=f"task_{datetime.now().timestamp()}",
                asin=asin,
                original_url=url
            )
        with cls._lock:
            cls._tasks[task.id] = task
        return task

    @classmethod
    def get_task(cls, task_id: str) -> ScrapeTask | None:
        return cls._tasks.get(task_id)

    @classmethod
    def get_all_tasks(cls) -> list[ScrapeTask]:
        with cls._lock:
            return sorted(cls._tasks.values(), key=lambda t: t.created_at, reverse=True)

    @classmethod
    def _execute_task(cls, task_id: str):
        """执行单个爬虫任务"""
        task = cls._tasks.get(task_id)
        if not task or not task.asin:
            return

        task.status = TaskStatus.RUNNING

        try:
            proxy_manager = ProxyManager(mode=ProxyMode.NONE)
            controller = ReviewPageController(proxy_manager=proxy_manager)
            extractor = ReviewExtractor()

            result = controller.open_review_page(task.asin)
            if result is None:
                task.status = TaskStatus.FAILED
                task.error = "页面打开失败"
                return

            try:
                page = result["page"]
                controller.load_more_reviews(page, max_pages=10)
                reviews = extractor.extract_all_reviews(page)
                task.review_count = len(reviews)
                task.status = TaskStatus.COMPLETED
            finally:
                controller.close_browser(result)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def start_executor(cls):
        """启动任务执行器"""
        if cls._executor_thread and cls._executor_thread.is_alive():
            return

        cls._running = True

        def executor():
            while cls._running:
                # 找pending任务执行
                task_id = None
                with cls._lock:
                    for tid, task in cls._tasks.items():
                        if task.status == TaskStatus.PENDING:
                            task_id = tid
                            break

                if task_id:
                    cls._execute_task(task_id)
                else:
                    threading.Event().wait(1)

        cls._executor_thread = threading.Thread(target=executor, daemon=True)
        cls._executor_thread.start()

    @classmethod
    def stop_executor(cls):
        cls._running = False
```

- [ ] **Step 2: 创建 web/routes/dashboard.py**

```python
"""Dashboard路由"""
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from services.scraper_service import ScraperService
from utils.decorators import login_required, get_current_user
from core.link_parser import LinkParser

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/dashboard")
@login_required
async def dashboard(request: Request):
    current_user = get_current_user(request)
    tasks = ScraperService.get_all_tasks()[:50]  # 最近50个任务

    # 解析显示用
    task_list = []
    for t in tasks:
        task_list.append({
            "id": t.id,
            "asin": t.asin,
            "original_url": t.original_url,
            "status": t.status.value,
            "review_count": t.review_count,
            "error": t.error,
            "created_at": t.created_at,
            "completed_at": t.completed_at
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "tasks": task_list
    })

@router.post("/dashboard/submit")
@login_required
async def submit_links(request: Request, urls: str = Form(...)):
    lines = [l.strip() for l in urls.strip().splitlines() if l.strip()]

    results = []
    for line in lines:
        parsed = LinkParser.parse(line)
        if parsed:
            task = ScraperService.add_task(parsed.original)
            results.append({"url": line, "asin": parsed.asin, "success": True})
        else:
            results.append({"url": line, "asin": "", "success": False, "error": "无法解析链接"})

    # 启动执行器
    ScraperService.start_executor()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": get_current_user(request),
        "tasks": [ScraperService.get_all_tasks()[:50]],
        "submit_results": results
    })
```

- [ ] **Step 3: 创建 web/templates/dashboard.html**

```html
{% extends "base.html" %}

{% block title %}首页 - Amazon评论爬虫{% endblock %}

{% block content %}
<div class="space-y-6">
    <h1 class="text-2xl font-bold">提交爬取任务</h1>

    <div class="bg-white rounded-lg shadow p-6">
        <form method="post" action="/dashboard/submit">
            <label class="block text-gray-700 text-sm font-bold mb-2">
                输入Amazon商品链接（支持多个，每行一个）
            </label>
            <textarea name="urls" rows="5" required
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://www.amazon.com/...&#10;https://www.amazon.com/..."></textarea>

            <button type="submit"
                class="mt-4 bg-blue-600 text-white font-bold py-2 px-6 rounded hover:bg-blue-700">
                开始爬取
            </button>
        </form>
    </div>

    {% if submit_results %}
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-bold mb-4">解析结果</h2>
        <div class="space-y-2">
            {% for r in submit_results %}
            <div class="flex items-center space-x-2">
                {% if r.success %}
                <span class="text-green-600">✓</span>
                <span>{{ r.asin }}</span>
                {% else %}
                <span class="text-red-600">✗</span>
                <span class="text-gray-500">{{ r.url }} - {{ r.error }}</span>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <h1 class="text-2xl font-bold">任务列表</h1>
    <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ASIN</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">评论数</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
                {% for task in tasks %}
                <tr>
                    <td class="px-4 py-3">{{ task.asin }}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-1 text-xs rounded
                            {% if task.status == 'completed' %}bg-green-100 text-green-800
                            {% elif task.status == 'running' %}bg-blue-100 text-blue-800
                            {% elif task.status == 'failed' %}bg-red-100 text-red-800
                            {% else %}bg-gray-100 text-gray-800{% endif %}">
                            {{ task.status }}
                        </span>
                    </td>
                    <td class="px-4 py-3">{{ task.review_count }}</td>
                    <td class="px-4 py-3 text-sm text-gray-500">{{ task.created_at }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% if not tasks %}
        <p class="p-4 text-gray-500 text-center">暂无任务</p>
        {% endif %}
    </div>
</div>

<script>
// 轮询更新任务状态
setInterval(() => {
    location.reload();
}, 10000);
</script>
{% endblock %}
```

- [ ] **Step 4: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): add dashboard with task submission"
```

---

### Task 4: 评论列表页面

**Files:**
- Create: `web/routes/reviews.py`
- Create: `web/templates/reviews.html`

- [ ] **Step 1: 创建 web/routes/reviews.py**

```python
"""评论列表路由"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

from database.store import DatabaseStore
from utils.decorators import login_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/reviews")
@login_required
async def reviews_page(
    request: Request,
    asin: str = Query(None),
    min_rating: int = Query(None, ge=1, le=5),
    max_rating: int = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1)
):
    current_user = get_current_user(request)
    db = DatabaseStore()

    # 获取评论
    all_reviews = db.get_all_reviews()

    # 筛选
    if asin:
        all_reviews = [r for r in all_reviews if r.asin == asin]
    if min_rating:
        all_reviews = [r for r in all_reviews if r.rating >= min_rating]
    if max_rating:
        all_reviews = [r for r in all_reviews if r.rating <= max_rating]

    # 分页
    page_size = 20
    total = len(all_reviews)
    start = (page - 1) * page_size
    end = start + page_size
    reviews = all_reviews[start:end]

    # 获取所有ASIN列表（用于筛选）
    asins = list(set(r.asin for r in db.get_all_reviews()))

    db.close()

    return templates.TemplateResponse("reviews.html", {
        "request": request,
        "current_user": current_user,
        "reviews": reviews,
        "asins": asins,
        "filters": {
            "asin": asin,
            "min_rating": min_rating,
            "max_rating": max_rating
        },
        "pagination": {
            "page": page,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    })
```

- [ ] **Step 2: 更新 database/store.py 添加 get_all_reviews 方法**

在 DatabaseStore 类中添加:
```python
def get_all_reviews(self) -> list:
    """获取所有评论"""
    self.cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
    rows = self.cursor.fetchall()
    return [Review(*row) for row in rows]
```

- [ ] **Step 3: 创建 web/templates/reviews.html**

```html
{% extends "base.html" %}

{% block title %}评论列表 - Amazon评论爬虫{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">评论列表</h1>

<div class="bg-white rounded-lg shadow p-4 mb-6">
    <form method="get" class="flex flex-wrap gap-4 items-end">
        <div>
            <label class="block text-gray-700 text-sm mb-1">ASIN筛选</label>
            <select name="asin" class="border rounded px-3 py-2">
                <option value="">全部</option>
                {% for a in asins %}
                <option value="{{ a }}" {% if filters.asin == a %}selected{% endif %}>{{ a }}</option>
                {% endfor %}
            </select>
        </div>
        <div>
            <label class="block text-gray-700 text-sm mb-1">最低评分</label>
            <input type="number" name="min_rating" min="1" max="5" value="{{ filters.min_rating or '' }}"
                class="border rounded px-3 py-2 w-20">
        </div>
        <div>
            <label class="block text-gray-700 text-sm mb-1">最高评分</label>
            <input type="number" name="max_rating" min="1" max="5" value="{{ filters.max_rating or '' }}"
                class="border rounded px-3 py-2 w-20">
        </div>
        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            筛选
        </button>
    </form>
</div>

<div class="bg-white rounded-lg shadow overflow-hidden">
    <table class="min-w-full">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ASIN</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">评分</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">内容</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vine</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
            {% for r in reviews %}
            <tr>
                <td class="px-4 py-3 text-sm">{{ r.asin }}</td>
                <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded
                        {% if r.rating <= 2 %}bg-red-100 text-red-800
                        {% elif r.rating == 3 %}bg-yellow-100 text-yellow-800
                        {% else %}bg-green-100 text-green-800{% endif %}">
                        {{ r.rating }}星
                    </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-500">{{ r.date }}</td>
                <td class="px-4 py-3 text-sm max-w-md truncate">{{ r.content[:100] }}...</td>
                <td class="px-4 py-3 text-sm">{{ '是' if r.is_vine else '否' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if not reviews %}
    <p class="p-4 text-gray-500 text-center">暂无评论数据</p>
    {% endif %}
</div>

{% if pagination.pages > 1 %}
<div class="mt-4 flex justify-center space-x-2">
    {% for p in range(1, pagination.pages + 1) %}
    <a href="?page={{ p }}&asin={{ filters.asin or '' }}"
        class="px-3 py-1 rounded {% if p == pagination.page %}bg-blue-600 text-white{% else %}bg-gray-200{% endif %}">
        {{ p }}
    </a>
    {% endfor %}
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 4: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): add reviews list page"
```

---

### Task 5: 数据分析页面

**Files:**
- Create: `web/routes/analytics.py`
- Create: `web/templates/analytics.html`
- Create: `web/services/analytics_service.py`

- [ ] **Step 1: 创建 web/services/analytics_service.py**

```python
"""分析服务"""
import sys
from pathlib import Path
from collections import Counter
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.store import DatabaseStore

class AnalyticsService:
    # 正面词
    POSITIVE_WORDS = {'great', 'excellent', 'amazing', 'good', 'love', 'perfect', 'best', 'awesome',
                      'wonderful', 'fantastic', 'highly', 'recommend', 'beautiful', 'easy', 'bright',
                      'quality', ' sturdy', 'nice', 'happy', 'satisfied'}

    # 负面词
    NEGATIVE_WORDS = {'bad', 'terrible', 'awful', 'poor', 'worst', 'horrible', 'disappointed',
                      'broken', 'defective', 'fail', 'failed', 'stopped', 'doesn't work', 'dont work',
                      'cheap', 'weak', 'dim', 'flickering', 'problem', 'issue', 'return', 'refund'}

    @classmethod
    def get_basic_stats(cls) -> dict:
        """基础统计"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        db.close()

        if not reviews:
            return {"total_reviews": 0, "total_products": 0, "avg_rating": 0, "rating_distribution": {}}

        total = len(reviews)
        products = len(set(r.asin for r in reviews))
        avg_rating = sum(r.rating for r in reviews) / total

        # 评分分布
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            distribution[int(r.rating)] = distribution.get(int(r.rating), 0) + 1

        return {
            "total_reviews": total,
            "total_products": products,
            "avg_rating": round(avg_rating, 2),
            "rating_distribution": distribution
        }

    @classmethod
    def get_keyword_analysis(cls, limit: int = 20) -> dict:
        """关键词分析"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        db.close()

        positive_words = []
        negative_words = []

        for r in reviews:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', r.content.lower())
            if r.rating >= 4:
                positive_words.extend(words)
            elif r.rating <= 2:
                negative_words.extend(words)

        # 过滤停用词
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her',
                     'was', 'one', 'our', 'out', 'have', 'been', 'they', 'this', 'that', 'with',
                     'would', 'there', 'their', 'what', 'about', 'which', 'when', 'make', 'like'}

        positive_counter = Counter(w for w in positive_words if w not in stopwords)
        negative_counter = Counter(w for w in negative_words if w not in stopwords)

        return {
            "positive": positive_counter.most_common(limit),
            "negative": negative_counter.most_common(limit)
        }

    @classmethod
    def get_sentiment_analysis(cls) -> dict:
        """情感分析"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        db.close()

        positive = 0
        negative = 0
        neutral = 0

        for r in reviews:
            text = r.content.lower()
            pos_count = sum(1 for w in cls.POSITIVE_WORDS if w in text)
            neg_count = sum(1 for w in cls.NEGATIVE_WORDS if w in text)

            if pos_count > neg_count:
                positive += 1
            elif neg_count > pos_count:
                negative += 1
            else:
                neutral += 1

        total = len(reviews)
        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "percentages": {
                "positive": round(positive / total * 100, 1) if total else 0,
                "negative": round(negative / total * 100, 1) if total else 0,
                "neutral": round(neutral / total * 100, 1) if total else 0
            }
        }

    @classmethod
    def get_time_trend(cls) -> list:
        """时间趋势 - 按月统计"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        db.close()

        monthly = {}
        for r in reviews:
            # 解析日期格式: "Reviewed in the United States on April 13, 2026"
            try:
                if 'on' in r.date:
                    parts = r.date.split('on')[-1].strip().split(',')
                    if len(parts) == 2:
                        month_year = parts[0].strip() + ',' + parts[1].strip()
                        if month_year not in monthly:
                            monthly[month_year] = {"count": 0, "total_rating": 0}
                        monthly[month_year]["count"] += 1
                        monthly[month_year]["total_rating"] += r.rating
            except:
                continue

        result = []
        for month, data in sorted(monthly.items()):
            avg = data["total_rating"] / data["count"] if data["count"] else 0
            result.append({
                "month": month,
                "count": data["count"],
                "avg_rating": round(avg, 2)
            })

        return result
```

- [ ] **Step 2: 创建 web/routes/analytics.py**

```python
"""分析路由"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from services.analytics_service import AnalyticsService
from utils.decorators import login_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/analytics")
@login_required
async def analytics_page(request: Request):
    current_user = get_current_user(request)

    stats = AnalyticsService.get_basic_stats()
    keywords = AnalyticsService.get_keyword_analysis()
    sentiment = AnalyticsService.get_sentiment_analysis()
    trend = AnalyticsService.get_time_trend()

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "current_user": current_user,
        "stats": stats,
        "keywords": keywords,
        "sentiment": sentiment,
        "trend": trend
    })
```

- [ ] **Step 3: 创建 web/templates/analytics.html**

```html
{% extends "base.html" %}

{% block title %}数据分析 - Amazon评论爬虫{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">数据分析</h1>

{% if stats.total_reviews == 0 %}
<div class="bg-white rounded-lg shadow p-8 text-center text-gray-500">
    暂无数据，请先爬取评论
</div>
{% else %}

<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-white rounded-lg shadow p-4">
        <div class="text-gray-500 text-sm">总评论数</div>
        <div class="text-3xl font-bold">{{ stats.total_reviews }}</div>
    </div>
    <div class="bg-white rounded-lg shadow p-4">
        <div class="text-gray-500 text-sm">商品数</div>
        <div class="text-3xl font-bold">{{ stats.total_products }}</div>
    </div>
    <div class="bg-white rounded-lg shadow p-4">
        <div class="text-gray-500 text-sm">平均评分</div>
        <div class="text-3xl font-bold">{{ stats.avg_rating }}</div>
    </div>
    <div class="bg-white rounded-lg shadow p-4">
        <div class="text-gray-500 text-sm">负面评论</div>
        <div class="text-3xl font-bold text-red-600">{{ sentiment.negative }}</div>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
    <div class="bg-white rounded-lg shadow p-4">
        <h2 class="text-lg font-bold mb-4">评分分布</h2>
        <div class="space-y-2">
            {% for star, count in stats.rating_distribution.items() %}
            <div class="flex items-center">
                <span class="w-12">{{ star }}星</span>
                <div class="flex-1 bg-gray-200 rounded-full h-4">
                    <div class="bg-blue-600 h-4 rounded-full"
                        style="width: {{ (count / stats.total_reviews * 100)|round }}%"></div>
                </div>
                <span class="ml-2 text-sm text-gray-500">{{ count }}</span>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="bg-white rounded-lg shadow p-4">
        <h2 class="text-lg font-bold mb-4">情感分析</h2>
        <div class="space-y-3">
            <div class="flex items-center justify-between">
                <span class="text-green-600">正面</span>
                <div class="flex-1 mx-4">
                    <div class="bg-gray-200 rounded-full h-4">
                        <div class="bg-green-500 h-4 rounded-full"
                            style="width: {{ sentiment.percentages.positive }}%"></div>
                    </div>
                </div>
                <span>{{ sentiment.percentages.positive }}%</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-gray-600">中性</span>
                <div class="flex-1 mx-4">
                    <div class="bg-gray-200 rounded-full h-4">
                        <div class="bg-gray-500 h-4 rounded-full"
                            style="width: {{ sentiment.percentages.neutral }}%"></div>
                    </div>
                </div>
                <span>{{ sentiment.percentages.neutral }}%</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-red-600">负面</span>
                <div class="flex-1 mx-4">
                    <div class="bg-gray-200 rounded-full h-4">
                        <div class="bg-red-500 h-4 rounded-full"
                            style="width: {{ sentiment.percentages.negative }}%"></div>
                    </div>
                </div>
                <span>{{ sentiment.percentages.negative }}%</span>
            </div>
        </div>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
    <div class="bg-white rounded-lg shadow p-4">
        <h2 class="text-lg font-bold mb-4">好评关键词</h2>
        <div class="flex flex-wrap gap-2">
            {% for word, count in keywords.positive[:15] %}
            <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                {{ word }} ({{ count }})
            </span>
            {% endfor %}
        </div>
    </div>
    <div class="bg-white rounded-lg shadow p-4">
        <h2 class="text-lg font-bold mb-4">差评关键词</h2>
        <div class="flex flex-wrap gap-2">
            {% for word, count in keywords.negative[:15] %}
            <span class="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                {{ word }} ({{ count }})
            </span>
            {% endfor %}
        </div>
    </div>
</div>

{% if trend %}
<div class="bg-white rounded-lg shadow p-4">
    <h2 class="text-lg font-bold mb-4">时间趋势</h2>
    <table class="min-w-full">
        <thead>
            <tr>
                <th class="px-4 py-2 text-left">月份</th>
                <th class="px-4 py-2 text-left">评论数</th>
                <th class="px-4 py-2 text-left">平均评分</th>
            </tr>
        </thead>
        <tbody>
            {% for t in trend %}
            <tr>
                <td class="px-4 py-2">{{ t.month }}</td>
                <td class="px-4 py-2">{{ t.count }}</td>
                <td class="px-4 py-2">{{ t.avg_rating }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% endif %}
{% endblock %}
```

- [ ] **Step 4: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): add analytics page with stats, keywords, sentiment, trend"
```

---

### Task 6: 使用说明页面

**Files:**
- Create: `web/routes/help.py`
- Create: `web/templates/help.html`

- [ ] **Step 1: 创建 web/routes/help.py**

```python
"""帮助页面路由"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from utils.decorators import login_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/help")
@login_required
async def help_page(request: Request):
    current_user = get_current_user(request)
    return templates.TemplateResponse("help.html", {
        "request": request,
        "current_user": current_user
    })
```

- [ ] **Step 2: 创建 web/templates/help.html**

```html
{% extends "base.html" %}

{% block title %}使用说明 - Amazon评论爬虫{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">使用说明</h1>

<div class="bg-white rounded-lg shadow p-6 space-y-6">
    <section>
        <h2 class="text-xl font-bold mb-3">1. 登录</h2>
        <p class="text-gray-600 mb-2">使用分配的账号密码登录系统。</p>
        <p class="text-gray-600">默认账号: <code class="bg-gray-100 px-2 py-1 rounded">admin</code> / <code class="bg-gray-100 px-2 py-1 rounded">admin123</code></p>
    </section>

    <hr>

    <section>
        <h2 class="text-xl font-bold mb-3">2. 提交爬取任务</h2>
        <ol class="list-decimal list-inside text-gray-600 space-y-2">
            <li>进入「首页」</li>
            <li>在文本框中粘贴Amazon商品链接，支持多个链接（每行一个）</li>
            <li>支持以下格式:
                <ul class="ml-8 list-disc">
                    <li>商品页: <code class="bg-gray-100 px-2 py-1 rounded">https://www.amazon.com/.../dp/B0XXXXX/</code></li>
                    <li>评论页: <code class="bg-gray-100 px-2 py-1 rounded">https://www.amazon.com/product-reviews/B0XXXXX/</code></li>
                    <li>纯ASIN: <code class="bg-gray-100 px-2 py-1 rounded">B0XXXXX</code></li>
                </ul>
            </li>
            <li>点击「开始爬取」</li>
            <li>系统会自动解析链接并创建爬取任务</li>
        </ol>
    </section>

    <hr>

    <section>
        <h2 class="text-xl font-bold mb-3">3. 查看任务状态</h2>
        <p class="text-gray-600 mb-2">任务列表显示所有爬取任务的状态:</p>
        <ul class="list-disc list-inside text-gray-600 space-y-1">
            <li><span class="inline-block w-3 h-3 bg-gray-400 rounded-full"></span> pending - 等待中</li>
            <li><span class="inline-block w-3 h-3 bg-blue-500 rounded-full"></span> running - 爬取中</li>
            <li><span class="inline-block w-3 h-3 bg-green-500 rounded-full"></span> completed - 已完成</li>
            <li><span class="inline-block w-3 h-3 bg-red-500 rounded-full"></span> failed - 失败</li>
        </ul>
        <p class="text-gray-500 text-sm mt-2">页面会自动刷新更新状态</p>
    </section>

    <hr>

    <section>
        <h2 class="text-xl font-bold mb-3">4. 查看评论列表</h2>
        <p class="text-gray-600 mb-2">在「评论列表」页面可以:</p>
        <ul class="list-disc list-inside text-gray-600 space-y-1">
            <li>查看所有爬取的评论</li>
            <li>按ASIN筛选特定商品</li>
            <li>按评分范围筛选</li>
            <li>分页浏览</li>
        </ul>
    </section>

    <hr>

    <section>
        <h2 class="text-xl font-bold mb-3">5. 数据分析</h2>
        <p class="text-gray-600 mb-2">「数据分析」页面提供:</p>
        <ul class="list-disc list-inside text-gray-600 space-y-1">
            <li><strong>基础统计</strong> - 总评论数、商品数、平均评分</li>
            <li><strong>评分分布</strong> - 各星级评论数量占比</li>
            <li><strong>情感分析</strong> - 正面/中性/负面评论比例</li>
            <li><strong>关键词分析</strong> - 好评和差评中的高频词</li>
            <li><strong>时间趋势</strong> - 按月份的评论数量和评分变化</li>
        </ul>
    </section>

    <hr>

    <section>
        <h2 class="text-xl font-bold mb-3">6. 导出数据</h2>
        <p class="text-gray-600">在评论列表页面可通过筛选后下载CSV文件，用Excel进一步分析。</p>
    </section>

    <hr>

    <section>
        <h2 class="text-xl font-bold mb-3">注意事项</h2>
        <ul class="list-disc list-inside text-gray-600 space-y-1">
            <li>爬取过程在后台进行，页面会自动刷新更新进度</li>
            <li>如果检测到验证码，任务会标记失败</li>
            <li>建议合理控制爬取频率，避免被限制</li>
            <li>数据仅存储在本地服务器</li>
        </ul>
    </section>
</div>
{% endblock %}
```

- [ ] **Step 3: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): add help page with user documentation"
```

---

### Task 7: 导出功能

**Files:**
- Create: `web/routes/export.py`

- [ ] **Step 1: 创建 web/routes/export.py**

```python
"""导出路由"""
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse

from database.store import DatabaseStore
from utils.decorators import login_required

router = APIRouter()

@router.get("/export")
@login_required
async def export_reviews(
    request: Request,
    asin: str = Query(None),
    min_rating: int = Query(None, ge=1, le=5)
):
    db = DatabaseStore()
    reviews = db.get_all_reviews()
    db.close()

    # 筛选
    if asin:
        reviews = [r for r in reviews if r.asin == asin]
    if min_rating:
        reviews = [r for r in reviews if r.rating >= min_rating]

    # 生成CSV
    def generate():
        yield "ASIN,Rating,Date,Brand,Content,Vine\n"
        for r in reviews:
            content = r.content.replace('"', '""').replace('\n', ' ')
            yield f'{r.asin},{r.rating},"{r.date}","{r.brand}","{content}","{"是" if r.is_vine else "否"}\n'

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reviews_export_{timestamp}.csv"

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

- [ ] **Step 2: 提交**

```bash
cd "D:/TK/亚马逊数据抓取"
git add web/
git commit -m "feat(web): add CSV export endpoint"
```

---

### Task 8: 运行脚本与测试

**Files:**
- Create: `run_web.py`

- [ ] **Step 1: 创建 run_web.py**

```python
#!/usr/bin/env python
"""启动Web服务"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from web.services.user_service import UserService

# 初始化数据库
UserService.init()

# 启动服务
import uvicorn
uvicorn.run("web.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: 测试启动**

```bash
cd "D:/TK/亚马逊数据抓取"
pip install fastapi uvicorn jinja2 python-multipart
python run_web.py
```

- [ ] **Step 3: 提交**

```bash
git add run_web.py
git commit -m "feat: add web service startup script"
```

---

## 自检清单

- [ ] Spec覆盖：登录认证 ✓, 链接提交 ✓, 任务列表 ✓, 评论列表 ✓, 数据分析 ✓, 导出 ✓, 说明文档 ✓
- [ ] 占位符检查：无TBD/TODO
- [ ] 类型一致性：方法签名、类名一致
- [ ] 现有代码复用：DatabaseStore, LinkParser, ReviewPageController, ReviewExtractor

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-29-amazon-review-scraper-web.md`**

---

**两种执行方式：**

**1. Subagent-Driven (推荐)** - 每个Task分配一个subagent完成，任务间有检查点

**2. Inline Execution** - 在当前session批量执行，有检查点

选择哪种方式？