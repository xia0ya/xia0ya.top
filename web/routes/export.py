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
    min_rating: int = Query(None, ge=1, le=5),
    max_rating: int = Query(None, ge=1, le=5)
):
    db = DatabaseStore()
    reviews = db.get_all_reviews()
    db.close()

    # 筛选
    if asin:
        reviews = [r for r in reviews if r.asin == asin]
    if min_rating:
        reviews = [r for r in reviews if r.rating >= min_rating]
    if max_rating:
        reviews = [r for r in reviews if r.rating <= max_rating]

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