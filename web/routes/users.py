"""用户管理路由"""
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from web.models.user import User, get_user_by_username, init_users_table, hash_password
from web.utils.decorators import login_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

def get_all_users():
    """获取所有用户"""
    import sqlite3
    from web.settings import DATABASE_PATH
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, username, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.get("/users")
@login_required
async def users_page(request: Request):
    current_user = get_current_user(request)
    users = get_all_users()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "current_user": current_user,
        "users": users
    })

@router.post("/users/add")
@login_required
async def add_user(request: Request, username: str = Form(...), password: str = Form(...)):
    import sqlite3
    from web.settings import DATABASE_PATH

    if not username or not password:
        return RedirectResponse(url="/users?error=empty", status_code=303)

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # 检查用户名是否已存在
    c.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    if c.fetchone()[0] > 0:
        conn.close()
        return RedirectResponse(url="/users?error=exists", status_code=303)

    # 添加用户
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
              (username, hash_password(password)))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/users?success=1", status_code=303)

@router.post("/users/delete")
@login_required
async def delete_user(request: Request, user_id: int = Form(...)):
    import sqlite3
    from web.settings import DATABASE_PATH

    # 不能删除自己
    current_user = get_current_user(request)
    user = get_user_by_username(current_user)

    if user and user.id == user_id:
        return RedirectResponse(url="/users?error=self", status_code=303)

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/users?success=1", status_code=303)
