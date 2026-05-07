"""评论列表路由"""
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database.store import DatabaseStore
from web.utils.decorators import login_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/reviews")
@login_required
async def reviews_page(
    request: Request,
    asin: str = Query(None),
    min_rating: str = Query(None),
    max_rating: str = Query(None),
    page: int = Query(1, ge=1)
):
    current_user = get_current_user(request)

    # 转换空字符串为None和int
    asin = asin if asin else None
    try:
        min_rating = int(min_rating) if min_rating else None
    except ValueError:
        min_rating = None
    try:
        max_rating = int(max_rating) if max_rating else None
    except ValueError:
        max_rating = None

    db = DatabaseStore()

    # 获取评论
    all_reviews = db.get_all_reviews()

    # 筛选
    if asin:
        all_reviews = [r for r in all_reviews if r.asin == asin]
    if min_rating is not None:
        all_reviews = [r for r in all_reviews if r.rating >= min_rating]
    if max_rating is not None:
        all_reviews = [r for r in all_reviews if r.rating <= max_rating]

    # 分页
    page_size = 20
    total = len(all_reviews)
    start = (page - 1) * page_size
    end = start + page_size
    reviews = all_reviews[start:end]

    # 获取所有ASIN列表（用于筛选）
    all_db_reviews = db.get_all_reviews()
    asins = list(set(r.asin for r in all_db_reviews))

    db.close()

    return templates.TemplateResponse("reviews.html", {
        "request": request,
        "current_user": current_user,
        "reviews": reviews,
        "asins": asins,
        "filters": {
            "asin": asin if asin else "",
            "min_rating": min_rating if min_rating else "",
            "max_rating": max_rating if max_rating else ""
        },
        "pagination": {
            "page": page,
            "total": total,
            "pages": (total + page_size - 1) // page_size if total > 0 else 0
        }
    })

@router.get("/reviews/export")
@login_required
async def export_reviews(request: Request, asin: str = Query(None)):
    """导出评论为CSV"""
    db = DatabaseStore()
    reviews = db.get_all_reviews()

    if asin:
        reviews = [r for r in reviews if r.asin == asin]

    # 生成CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ASIN', '评分', '日期', '内容', 'Vine', '采集时间'])
    for r in reviews:
        writer.writerow([r.asin, r.rating, r.date, r.content, '是' if r.is_vine else '否', r.collected_at])

    db.close()

    filename = f"reviews_{asin or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@router.post("/reviews/delete")
@login_required
async def delete_reviews(request: Request, asin: str = Form(...)):
    """删除指定ASIN的所有评论"""
    db = DatabaseStore()
    db.conn.execute("DELETE FROM reviews WHERE asin = ?", (asin,))
    db.conn.commit()
    db.close()

    return RedirectResponse(url="/reviews", status_code=303)