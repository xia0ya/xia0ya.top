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