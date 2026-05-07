"""分析服务"""
import json
from collections import Counter
import re
from pathlib import Path

from database.store import DatabaseStore
from web.services.wordcloud_service import WordCloudGenerator

class AnalyticsService:
    # 正面词
    POSITIVE_WORDS = {'great', 'excellent', 'amazing', 'good', 'love', 'perfect', 'best', 'awesome',
                      'wonderful', 'fantastic', 'highly', 'recommend', 'beautiful', 'easy', 'bright',
                      'quality', 'sturdy', 'nice', 'happy', 'satisfied'}

    # 负面词
    NEGATIVE_WORDS = {'bad', 'terrible', 'awful', 'poor', 'worst', 'horrible', 'disappointed',
                      'broken', 'defective', 'fail', 'failed', 'stopped', "doesn't work", 'dont work',
                      'cheap', 'weak', 'dim', 'flickering', 'problem', 'issue', 'return', 'refund'}

    @classmethod
    def _apply_filters(cls, reviews, asin=None, min_rating=None, max_rating=None):
        """应用筛选条件"""
        if asin:
            reviews = [r for r in reviews if r.asin == asin]
        if min_rating:
            reviews = [r for r in reviews if r.rating >= min_rating]
        if max_rating:
            reviews = [r for r in reviews if r.rating <= max_rating]
        return reviews

    @classmethod
    def get_basic_stats(cls, asin=None, min_rating=None, max_rating=None) -> dict:
        """基础统计"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        reviews = cls._apply_filters(reviews, asin, min_rating, max_rating)
        db.close()

        if not reviews:
            return {"total_reviews": 0, "total_products": 0, "avg_rating": 0, "rating_distribution": {}}

        total = len(reviews)
        products = len(set(r.asin for r in reviews))
        avg_rating = sum(r.rating for r in reviews) / total

        # 评分分布
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            distribution[int(r.rating)] = distribution.get(int(r.rating), 0) + 1

        return {
            "total_reviews": total,
            "total_products": products,
            "avg_rating": round(avg_rating, 2),
            "rating_distribution": distribution
        }

    @classmethod
    def get_keyword_analysis(cls, asin=None, min_rating=None, max_rating=None, limit: int = 20) -> dict:
        """关键词分析"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        reviews = cls._apply_filters(reviews, asin, min_rating, max_rating)
        db.close()

        positive_words = []
        negative_words = []

        for r in reviews:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', r.content.lower())
            if r.rating >= 4:
                positive_words.extend(words)
            elif r.rating <= 2:
                negative_words.extend(words)

        # 过滤停用词
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her',
                     'was', 'one', 'our', 'out', 'have', 'been', 'they', 'this', 'that', 'with',
                     'would', 'there', 'their', 'what', 'about', 'which', 'when', 'make', 'like'}

        positive_counter = Counter(w for w in positive_words if w not in stopwords)
        negative_counter = Counter(w for w in negative_words if w not in stopwords)

        return {
            "positive": positive_counter.most_common(limit),
            "negative": negative_counter.most_common(limit)
        }

    @classmethod
    def get_sentiment_analysis(cls, asin=None, min_rating=None, max_rating=None) -> dict:
        """情感分析"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        reviews = cls._apply_filters(reviews, asin, min_rating, max_rating)
        db.close()

        positive = 0
        negative = 0
        neutral = 0

        for r in reviews:
            text = r.content.lower()
            pos_count = sum(1 for w in cls.POSITIVE_WORDS if w in text)
            neg_count = sum(1 for w in cls.NEGATIVE_WORDS if w in text)

            if pos_count > neg_count:
                positive += 1
            elif neg_count > pos_count:
                negative += 1
            else:
                neutral += 1

        total = len(reviews)
        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "percentages": {
                "positive": round(positive / total * 100, 1) if total else 0,
                "negative": round(negative / total * 100, 1) if total else 0,
                "neutral": round(neutral / total * 100, 1) if total else 0
            }
        }

    @classmethod
    def get_time_trend(cls, asin=None, min_rating=None, max_rating=None) -> list:
        """时间趋势 - 按月统计"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        reviews = cls._apply_filters(reviews, asin, min_rating, max_rating)
        db.close()

        monthly = {}
        for r in reviews:
            # 解析日期格式: "Reviewed in the United States on April 13, 2026"
            try:
                if 'on' in r.date:
                    parts = r.date.split('on')[-1].strip().split(',')
                    if len(parts) == 2:
                        month_year = parts[0].strip() + ',' + parts[1].strip()
                        if month_year not in monthly:
                            monthly[month_year] = {"count": 0, "total_rating": 0}
                        monthly[month_year]["count"] += 1
                        monthly[month_year]["total_rating"] += r.rating
            except:
                continue

        result = []
        for month, data in sorted(monthly.items()):
            avg = data["total_rating"] / data["count"] if data["count"] else 0
            result.append({
                "month": month,
                "count": data["count"],
                "avg_rating": round(avg, 2)
            })

        return result

    @classmethod
    def get_wordcloud(cls, asin=None, min_rating=None, max_rating=None) -> dict:
        """词云生成"""
        db = DatabaseStore()
        reviews = db.get_all_reviews()
        reviews = cls._apply_filters(reviews, asin, min_rating, max_rating)
        db.close()

        if not reviews:
            return {"wordcloud_path": None, "frequency_path": None}

        generator = WordCloudGenerator()
        img_path, freq_path = generator.generate(reviews, save_dir="web/static/wordcloud")

        return {
            "wordcloud_path": f"/static/wordcloud/wordcloud.png" if img_path else None,
            "frequency_path": freq_path
        }
