"""认证路由"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from web.services.user_service import UserService

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