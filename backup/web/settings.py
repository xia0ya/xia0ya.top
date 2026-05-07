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
