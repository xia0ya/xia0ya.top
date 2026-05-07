"""爬虫任务服务"""
import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import sys
from pathlib import Path

# 项目根目录（cookies.json所在位置）
PROJECT_ROOT = Path(__file__).parent.parent.parent
COOKIES_PATH = str(PROJECT_ROOT / "cookies.json")

sys.path.insert(0, str(PROJECT_ROOT))

from proxy.manager import ProxyManager, ProxyMode
from scraper.review_page import ReviewPageController
from scraper.review_extractor import ReviewExtractor
from core.link_parser import LinkParser
from database.store import DatabaseStore, Review
from datetime import datetime as dt

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
    _current_task_id: Optional[str] = None  # 当前执行中的任务ID

    @classmethod
    def add_task(cls, url: str) -> tuple[ScrapeTask, bool]:
        """添加爬虫任务，返回(任务, 是否新建)"""
        asin = LinkParser.extract_asin(url)
        if not asin:
            task = ScrapeTask(
                id=f"task_{datetime.now().timestamp()}",
                asin="",
                original_url=url,
                status=TaskStatus.FAILED,
                error="无法提取ASIN"
            )
            with cls._lock:
                cls._tasks[task.id] = task
            return task, True

        with cls._lock:
            # 检查是否有相同ASIN的PENDING/RUNNING任务
            for tid, task in cls._tasks.items():
                if task.asin == asin and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                    return task, False  # 返回已有任务，不创建新的

            task = ScrapeTask(
                id=f"task_{datetime.now().timestamp()}",
                asin=asin,
                original_url=url
            )
            cls._tasks[task.id] = task
            return task, True

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
        cls._current_task_id = task_id

        try:
            proxy_manager = ProxyManager(mode=ProxyMode.NONE)
            controller = ReviewPageController(proxy_manager=proxy_manager, cookies_path=COOKIES_PATH)
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

                # 保存到数据库
                if reviews:
                    db = DatabaseStore()
                    db_reviews = [
                        Review(
                            asin=task.asin,
                            brand="",  # 品牌待定
                            rating=r.rating,
                            date=r.date,
                            content=r.content,
                            is_vine=r.is_vine,
                            collected_at=dt.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        for r in reviews
                    ]
                    db.insert_reviews(db_reviews)
                    db.close()
            finally:
                controller.close_browser(result)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cls._current_task_id = None

    @classmethod
    def get_current_task(cls) -> Optional[str]:
        """获取当前正在执行的任务ID"""
        return cls._current_task_id

    @classmethod
    def stop_task(cls, task_id: str) -> bool:
        """停止指定任务"""
        with cls._lock:
            task = cls._tasks.get(task_id)
            if task and task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.FAILED
                task.error = "用户停止"
                task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True
            return False

    @classmethod
    def delete_task(cls, task_id: str) -> bool:
        """删除任务"""
        with cls._lock:
            if task_id in cls._tasks:
                del cls._tasks[task_id]
                return True
            return False

    @classmethod
    def stop_all(cls):
        """停止所有任务"""
        with cls._lock:
            for task in cls._tasks.values():
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.FAILED
                    task.error = "用户停止"
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
        cls._current_task_id = None
        cls.stop_all()