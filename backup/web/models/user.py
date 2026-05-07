"""用户模型"""
import sqlite3
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from web.settings import DATABASE_PATH

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