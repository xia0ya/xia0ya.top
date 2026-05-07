"""分析路由"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

from web.services.analytics_service import AnalyticsService
from web.utils.decorators import login_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/analytics")
@login_required
async def analytics_page(
    request: Request,
    asin: str = Query(None),
    min_rating: str = Query(None),
    max_rating: str = Query(None)
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

    # 获取过滤条件
    filters = {"asin": asin, "min_rating": min_rating, "max_rating": max_rating}

    stats = AnalyticsService.get_basic_stats(asin=asin, min_rating=min_rating, max_rating=max_rating)
    keywords = AnalyticsService.get_keyword_analysis(asin=asin, min_rating=min_rating, max_rating=max_rating)
    sentiment = AnalyticsService.get_sentiment_analysis(asin=asin, min_rating=min_rating, max_rating=max_rating)
    trend = AnalyticsService.get_time_trend(asin=asin, min_rating=min_rating, max_rating=max_rating)
    wordcloud = AnalyticsService.get_wordcloud(asin=asin, min_rating=min_rating, max_rating=max_rating)

    # 获取所有ASIN用于筛选器
    from database.store import DatabaseStore
    db = DatabaseStore()
    all_reviews = db.get_all_reviews()
    asins = list(set(r.asin for r in all_reviews))
    db.close()

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "current_user": current_user,
        "stats": stats,
        "keywords": keywords,
        "sentiment": sentiment,
        "trend": trend,
        "wordcloud": wordcloud,
        "filters": filters,
        "asins": asins
    })
