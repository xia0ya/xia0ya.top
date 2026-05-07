"""Review extractor for extracting negative reviews from Amazon product pages."""

from dataclasses import dataclass
from typing import List, Optional

from playwright.sync_api import Page, Locator


@dataclass
class ExtractedReview:
    """Represents an extracted review from an Amazon product page.

    Attributes:
        rating: The star rating (0.0 to 5.0).
        date: The review date string.
        content: The review text content.
        is_vine: Whether the review is from a Vine verified purchaser.
    """
    rating: float
    date: str
    content: str
    is_vine: bool


class ReviewExtractor:
    """Extracts negative reviews (3 stars and below) from Amazon review pages.

    Uses data-hook attributes to locate and extract review elements,
    filtering for negative reviews and identifying Vine verified badges.
    """

    # data-hook selectors for Amazon review elements
    SELECTOR_REVIEW_CONTAINER = "[data-hook='review']"
    SELECTOR_STAR_RATING = "[data-hook='review-star-rating'], [data-hook='cmps-review-star-rating']"
    SELECTOR_REVIEW_BODY = "[data-hook='review-body']"
    SELECTOR_REVIEW_DATE = "[data-hook='review-date']"
    SELECTOR_VINE_BADGE = "[data-hook='vine-badge']"
    SELECTOR_VERIFIED_PURCHASE = "[data-hook='verified-badge']"

    def extract_negative_reviews(self, page: Page) -> List[ExtractedReview]:
        """Extract all negative reviews (3 stars and below) from the page.

        Args:
            page: Playwright Page object containing reviews.

        Returns:
            List of ExtractedReview objects with rating <= 3.0.
        """
        review_elements = self._get_review_elements(page)
        negative_reviews = []

        for element in review_elements:
            rating = self._extract_rating(element)
            if rating is not None and rating <= 3.0:
                date = self._extract_date(element)
                content = self._extract_content(element)
                is_vine = self._is_vine_review(element)

                negative_reviews.append(ExtractedReview(
                    rating=rating,
                    date=date,
                    content=content,
                    is_vine=is_vine
                ))

        return negative_reviews

    def extract_all_reviews(self, page: Page) -> List[ExtractedReview]:
        """Extract all reviews from the page using JavaScript.

        Args:
            page: Playwright Page object containing reviews.

        Returns:
            List of ExtractedReview objects for all reviews on the page.
        """
        # 等待页面稳定
        page.wait_for_timeout(3000)

        # 用 JS 提取所有评论数据
        reviews_data = page.evaluate("""
            () => {
                const reviews = [];
                const reviewEls = document.querySelectorAll('[data-hook="review"]');
                reviewEls.forEach(el => {
                    // 提取评分
                    let rating = null;
                    const ratingEl = el.querySelector('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]');
                    if (ratingEl) {
                        const match = ratingEl.textContent.match(/([\\d.]+)/);
                        if (match) rating = parseFloat(match[1]);
                    }

                    // 提取日期
                    let date = '';
                    const dateEl = el.querySelector('[data-hook="review-date"]');
                    if (dateEl) date = dateEl.textContent;

                    // 提取内容
                    let content = '';
                    const bodyEl = el.querySelector('[data-hook="review-body"]');
                    if (bodyEl) content = bodyEl.innerText;

                    // 检查Vine
                    const vineEl = el.querySelector('[data-hook="vine-badge"]');
                    const isVine = vineEl !== null;

                    if (rating !== null) {
                        reviews.push({ rating, date, content, is_vine: isVine });
                    }
                });
                return reviews;
            }
        """)

        print(f"  -> JS提取到 {len(reviews_data)} 条评论")

        return [
            ExtractedReview(
                rating=r["rating"],
                date=r["date"],
                content=r["content"],
                is_vine=r["is_vine"]
            )
            for r in reviews_data
        ]

    def extract_reviews(
        self,
        page: Page,
        min_rating: Optional[float] = None
    ) -> List[ExtractedReview]:
        """Extract reviews from the page, optionally filtered by rating.

        Uses JavaScript extraction for consistent and complete data extraction.

        Args:
            page: Playwright Page object containing reviews.
            min_rating: Minimum rating to include (None = include all).

        Returns:
            List of ExtractedReview objects.
        """
        # 等待页面稳定
        page.wait_for_timeout(3000)

        # 用 JS 提取所有评论数据
        reviews_data = page.evaluate("""
            () => {
                const reviews = [];
                const reviewEls = document.querySelectorAll('[data-hook="review"]');
                reviewEls.forEach(el => {
                    // 提取评分
                    let rating = null;
                    const ratingEl = el.querySelector('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]');
                    if (ratingEl) {
                        const match = ratingEl.textContent.match(/([\\d.]+)/);
                        if (match) rating = parseFloat(match[1]);
                    }

                    // 提取日期
                    let date = '';
                    const dateEl = el.querySelector('[data-hook="review-date"]');
                    if (dateEl) date = dateEl.textContent;

                    // 提取内容
                    let content = '';
                    const bodyEl = el.querySelector('[data-hook="review-body"]');
                    if (bodyEl) content = bodyEl.innerText;

                    // 检查Vine
                    const vineEl = el.querySelector('[data-hook="vine-badge"]');
                    const isVine = vineEl !== null;

                    if (rating !== null) {
                        reviews.push({ rating, date, content, is_vine: isVine });
                    }
                });
                return reviews;
            }
        """)

        print(f"  -> JS提取到 {len(reviews_data)} 条评论")

        result = []
        for r in reviews_data:
            if min_rating is not None and r["rating"] < min_rating:
                continue
            result.append(ExtractedReview(
                rating=r["rating"],
                date=r["date"],
                content=r["content"],
                is_vine=r["is_vine"]
            ))

        return result

    def _get_review_elements(self, page: Page) -> List[Locator]:
        """Get all review container elements from the page.

        Args:
            page: Playwright Page object.

        Returns:
            List of Locator objects for each review container.
        """
        return page.locator(self.SELECTOR_REVIEW_CONTAINER).all()

    def _extract_rating(self, element: Locator) -> Optional[float]:
        """Extract the star rating from a review element.

        Args:
            element: Review container Locator.

        Returns:
            Rating as float, or None if not found.
        """
        try:
            rating_locator = element.locator(self.SELECTOR_STAR_RATING)
            rating_text = rating_locator.inner_text()
            if rating_text:
                # Rating format: "4.5 out of 5 stars" or similar
                parts = rating_text.split()
                if parts:
                    try:
                        return float(parts[0])
                    except ValueError:
                        pass
            return None
        except Exception:
            return None

    def _extract_date(self, element: Locator) -> str:
        """Extract the review date from a review element.

        Args:
            element: Review container Locator.

        Returns:
            Date string from the review element, empty string if not found.
        """
        try:
            date_locator = element.locator(self.SELECTOR_REVIEW_DATE)
            return date_locator.inner_text()
        except Exception:
            return ""

    def _extract_content(self, element: Locator) -> str:
        """Extract the review content from a review element.

        Args:
            element: Review container Locator.

        Returns:
            Review text content, empty string if not found.
        """
        try:
            body_locator = element.locator(self.SELECTOR_REVIEW_BODY)
            return body_locator.inner_text()
        except Exception:
            return ""

    def _is_vine_review(self, element: Locator) -> bool:
        """Check if the review has a Vine verified badge.

        Args:
            element: Review container Locator.

        Returns:
            True if the review is from a Vine verified purchaser.
        """
        try:
            vine_locator = element.locator(self.SELECTOR_VINE_BADGE)
            return vine_locator.count() > 0
        except Exception:
            return False
