"""帮助页面路由"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from web.utils.decorators import login_required, get_current_user

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
