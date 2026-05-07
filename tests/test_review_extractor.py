"""Tests for scraper/review_extractor.py"""

import pytest
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.review_extractor import ExtractedReview, ReviewExtractor


class TestExtractedReview:
    """Test ExtractedReview dataclass."""

    def test_extracted_review_creation(self):
        """Test creating an ExtractedReview instance."""
        review = ExtractedReview(
            rating=2.5,
            date="2024-01-15",
            content="Poor quality, broke after one week",
            is_vine=False
        )
        assert review.rating == 2.5
        assert review.date == "2024-01-15"
        assert review.content == "Poor quality, broke after one week"
        assert review.is_vine is False

    def test_extracted_review_with_vine(self):
        """Test ExtractedReview with Vine badge."""
        review = ExtractedReview(
            rating=3.0,
            date="2024-02-20",
            content="It's okay but not great",
            is_vine=True
        )
        assert review.rating == 3.0
        assert review.is_vine is True


class TestReviewExtractor:
    """Test ReviewExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a ReviewExtractor instance."""
        return ReviewExtractor()

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page with review data."""
        page = MagicMock()

        # Sample review HTML elements
        def create_mock_locator(reviews_data):
            locators = []
            for data in reviews_data:
                mock_element = MagicMock()
                mock_element.inner_text = data.get("text", "")
                mock_element.get_attribute = lambda attr, d=data: d.get("attrs", {}).get(attr, "")
                locators.append(mock_element)
            return locators

        def mock_all(selector):
            if "review-star-rating" in selector or "rating" in selector:
                return [r["rating"]] if isinstance(r, int) else []
            elif "review-body" in selector or "content" in selector:
                return [r["content"] for r in reviews_data]
            elif "review-date" in selector or "date" in selector:
                return [r["date"] for r in reviews_data]
            return []

        def mock_locator(selector):
            mock_loc = MagicMock()
            mock_loc.count = lambda: len(reviews_data)
            mock_loc.all = lambda: [
                MagicMock(
                    inner_text=r.get("content", ""),
                    get_attribute=lambda attr, rev=r: rev.get("attrs", {}).get(attr, "")
                )
                for r in reviews_data
            ]
            mock_loc.first = MagicMock()
            return mock_loc

        page.locator = mock_locator
        return page

    def test_extract_negative_reviews_filters_low_ratings(self, extractor, mock_page):
        """Test that only ratings <= 3 are extracted."""
        reviews_data = [
            {"rating": 5.0, "date": "2024-01-01", "content": "Excellent!", "is_vine": False},
            {"rating": 1.0, "date": "2024-01-02", "content": "Terrible product", "is_vine": False},
            {"rating": 3.0, "date": "2024-01-03", "content": "Average, expected more", "is_vine": True},
            {"rating": 4.0, "date": "2024-01-04", "content": "Pretty good", "is_vine": False},
            {"rating": 2.0, "date": "2024-01-05", "content": "Disappointed", "is_vine": False},
        ]

        mock_page.reviews_data = reviews_data
        mock_page.locator = lambda s: create_mock_locator_for_reviews(reviews_data, s)

        # Create mock locators that behave like real review element locators
        mock_elements = [
            create_mock_review_element(r) for r in reviews_data
        ]

        with patch.object(extractor, '_get_review_elements', return_value=mock_elements):
            result = extractor.extract_negative_reviews(mock_page)

        assert all(r.rating <= 3 for r in result)
        assert len(result) == 3  # 1 star, 3 star, 2 star

    def test_extract_negative_reviews_excludes_high_ratings(self, extractor, mock_page):
        """Test that ratings > 3 are not extracted."""
        reviews_data = [
            {"rating": 5.0, "date": "2024-01-01", "content": "Excellent!", "is_vine": False},
            {"rating": 4.0, "date": "2024-01-02", "content": "Pretty good", "is_vine": False},
            {"rating": 4.5, "date": "2024-01-03", "content": "Very satisfied", "is_vine": True},
        ]

        with patch.object(extractor, '_get_review_elements', return_value=reviews_data):
            result = extractor.extract_negative_reviews(mock_page)

        assert len(result) == 0

    def test_extract_negative_reviews_identifies_vine(self, extractor):
        """Test that Vine badges are correctly identified."""
        vine_reviews = [
            {"rating": 2.0, "date": "2024-01-01", "content": "Bad", "is_vine": True},
            {"rating": 3.0, "date": "2024-01-02", "content": "Okay", "is_vine": True},
        ]

        mock_elements = [
            create_mock_review_element(r) for r in vine_reviews
        ]

        with patch.object(extractor, '_get_review_elements', return_value=mock_elements):
            result = extractor.extract_negative_reviews(MagicMock())

        assert all(r.is_vine for r in result)

    def test_extract_negative_reviews_empty_page(self, extractor):
        """Test extraction from page with no reviews."""
        with patch.object(extractor, '_get_review_elements', return_value=[]):
            result = extractor.extract_negative_reviews(MagicMock())

        assert result == []

    def test_extract_negative_reviews_all_negative(self, extractor):
        """Test extraction when all reviews are negative."""
        reviews_data = [
            {"rating": 1.0, "date": "2024-01-01", "content": "Terrible", "is_vine": False},
            {"rating": 2.0, "date": "2024-01-02", "content": "Poor", "is_vine": False},
            {"rating": 3.0, "date": "2024-01-03", "content": "Mediocre", "is_vine": False},
        ]

        mock_elements = [
            create_mock_review_element(r) for r in reviews_data
        ]

        with patch.object(extractor, '_get_review_elements', return_value=mock_elements):
            result = extractor.extract_negative_reviews(MagicMock())

        assert len(result) == 3


def create_mock_locator_for_reviews(reviews_data, selector):
    """Helper to create mock locators matching the selector."""
    mock_loc = MagicMock()

    if "star-rating" in selector.lower() or ("rating" in selector.lower() and "review" in selector.lower()):
        mock_loc.all = lambda: [
            MagicMock(
                inner_text=str(r["rating"]),
                get_attribute=lambda attr, rev=r: {"class": "rating"}.get(attr, "")
            )
            for r in reviews_data
        ]
    elif "body" in selector.lower() or "content" in selector.lower():
        mock_loc.all = lambda: [MagicMock(inner_text=r["content"]) for r in reviews_data]
    elif "date" in selector.lower():
        mock_loc.all = lambda: [MagicMock(inner_text=r["date"]) for r in reviews_data]
    elif "vine" in selector.lower() or "verified" in selector.lower():
        mock_loc.all = lambda: [
            MagicMock(
                inner_text="Vine" if r.get("is_vine") else "",
                get_attribute=lambda attr, rev=r: {"class": "vine-badge"}.get(attr, "")
            )
            for r in reviews_data
        ]
    else:
        mock_loc.all = lambda: []

    mock_loc.count = lambda: len(reviews_data)
    return mock_loc


def create_mock_review_element(data):
    """Create a mock review element with proper locator chain."""
    element = MagicMock()

    # Rating sub-locator
    rating_loc = MagicMock()
    rating_loc.get_attribute = lambda attr: f"{data['rating']} out of 5 stars"
    element.locator = lambda s: {
        "[data-hook='review-star-rating']": rating_loc,
        "[data-hook='review-body']": MagicMock(inner_text=data["content"]),
        "[data-hook='review-date']": MagicMock(inner_text=data["date"]),
        "[data-hook='vine-badge']": MagicMock(count=lambda: 1 if data.get("is_vine") else 0),
    }.get(s, MagicMock(count=lambda: 0, inner_text="", get_attribute=lambda attr: ""))

    return element
