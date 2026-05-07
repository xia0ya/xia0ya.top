"""Dashboard路由"""
import json
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

PROJECT_ROOT = Path(__file__).parent.parent.parent
COOKIES_PATH = PROJECT_ROOT / "cookies.json"

from web.services.scraper_service import ScraperService, TaskStatus
from web.utils.decorators import login_required, get_current_user
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
            task, is_new = ScraperService.add_task(parsed.original)
            if is_new:
                results.append({"url": line, "asin": parsed.asin, "success": True})
            else:
                results.append({"url": line, "asin": parsed.asin, "success": False, "error": "任务已在队列中"})
        else:
            results.append({"url": line, "asin": "", "success": False, "error": "无法解析链接"})

    # 启动执行器
    ScraperService.start_executor()

    current_user = get_current_user(request)
    tasks = ScraperService.get_all_tasks()[:50]
    task_list = [{
        "id": t.id, "asin": t.asin, "original_url": t.original_url,
        "status": t.status.value, "review_count": t.review_count,
        "error": t.error, "created_at": t.created_at, "completed_at": t.completed_at
    } for t in tasks]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "tasks": task_list,
        "submit_results": results
    })

@router.post("/dashboard/cookie")
@login_required
async def save_cookie(request: Request, cookies_json: str = Form(...)):
    success = False
    try:
        # 验证 JSON 格式
        cookies = json.loads(cookies_json)
        if isinstance(cookies, list) and len(cookies) > 0:
            with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            success = True
    except json.JSONDecodeError:
        pass

    current_user = get_current_user(request)
    tasks = ScraperService.get_all_tasks()[:50]
    task_list = [{
        "id": t.id, "asin": t.asin, "original_url": t.original_url,
        "status": t.status.value, "review_count": t.review_count,
        "error": t.error, "created_at": t.created_at, "completed_at": t.completed_at
    } for t in tasks]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "tasks": task_list,
        "cookie_success": success
    })

@router.post("/dashboard/stop")
@login_required
async def stop_tasks(request: Request):
    ScraperService.stop_executor()
    current_user = get_current_user(request)
    tasks = ScraperService.get_all_tasks()[:50]
    task_list = [{
        "id": t.id, "asin": t.asin, "original_url": t.original_url,
        "status": t.status.value, "review_count": t.review_count,
        "error": t.error, "created_at": t.created_at, "completed_at": t.completed_at
    } for t in tasks]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "tasks": task_list
    })

@router.post("/dashboard/stop-one")
@login_required
async def stop_single_task(request: Request, task_id: str = Form(...)):
    ScraperService.stop_task(task_id)
    current_user = get_current_user(request)
    tasks = ScraperService.get_all_tasks()[:50]
    task_list = [{
        "id": t.id, "asin": t.asin, "original_url": t.original_url,
        "status": t.status.value, "review_count": t.review_count,
        "error": t.error, "created_at": t.created_at, "completed_at": t.completed_at
    } for t in tasks]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "tasks": task_list
    })

@router.post("/dashboard/delete-task")
@login_required
async def delete_task(request: Request, task_id: str = Form(...)):
    ScraperService.delete_task(task_id)
    current_user = get_current_user(request)
    tasks = ScraperService.get_all_tasks()[:50]
    task_list = [{
        "id": t.id, "asin": t.asin, "original_url": t.original_url,
        "status": t.status.value, "review_count": t.review_count,
        "error": t.error, "created_at": t.created_at, "completed_at": t.completed_at
    } for t in tasks]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "tasks": task_list
    })

@router.get("/api/tasks/status")
async def api_tasks_status():
    """API: 获取任务状态（用于前端轮询）"""
    tasks = ScraperService.get_all_tasks()[:50]
    has_running = any(t.status == TaskStatus.RUNNING for t in tasks)
    task_list = [{
        "id": t.id,
        "asin": t.asin,
        "status": t.status.value,
        "review_count": t.review_count
    } for t in tasks]
    return {"tasks": task_list, "has_running": has_running}