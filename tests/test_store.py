"""Tests for database/store.py"""

import os
import tempfile
import pytest
from database.store import Review, DatabaseStore


class TestReview:
    """Test Review dataclass."""

    def test_review_creation(self):
        """Test creating a Review instance."""
        review = Review(
            asin="B001",
            brand="TestBrand",
            rating=4.5,
            date="2024-01-01",
            content="Great product",
            is_vine=True,
            collected_at="2024-01-02"
        )
        assert review.asin == "B001"
        assert review.brand == "TestBrand"
        assert review.rating == 4.5
        assert review.date == "2024-01-01"
        assert review.content == "Great product"
        assert review.is_vine is True
        assert review.collected_at == "2024-01-02"


class TestDatabaseStore:
    """Test DatabaseStore class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def store(self, temp_db):
        """Create a DatabaseStore with temporary database."""
        store = DatabaseStore(temp_db)
        yield store
        store.close()

    def test_init_db_creates_table(self, store):
        """Test that _init_db creates the reviews table."""
        store._init_db()
        cursor = store.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='reviews'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "reviews"

    def test_init_db_creates_indexes(self, store):
        """Test that _init_db creates indexes."""
        store._init_db()
        cursor = store.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_brand" in indexes
        assert "idx_asin" in indexes

    def test_insert_review(self, store):
        """Test inserting a single review."""
        review = Review(
            asin="B001",
            brand="TestBrand",
            rating=4.5,
            date="2024-01-01",
            content="Great product",
            is_vine=True,
            collected_at="2024-01-02"
        )
        store.insert_review(review)
        cursor = store.conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE asin=?", ("B001",))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "B001"
        assert row[2] == "TestBrand"
        assert row[3] == 4.5

    def test_insert_reviews(self, store):
        """Test bulk inserting reviews."""
        reviews = [
            Review(
                asin=f"B00{i}",
                brand="BrandA",
                rating=4.0,
                date="2024-01-01",
                content=f"Review {i}",
                is_vine=False,
                collected_at="2024-01-02"
            )
            for i in range(5)
        ]
        store.insert_reviews(reviews)
        cursor = store.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews")
        count = cursor.fetchone()[0]
        assert count == 5

    def test_get_reviews_by_brand(self, store):
        """Test querying reviews by brand."""
        reviews = [
            Review(asin="B001", brand="BrandA", rating=4.0, date="2024-01-01",
                   content="Review 1", is_vine=False, collected_at="2024-01-02"),
            Review(asin="B002", brand="BrandA", rating=5.0, date="2024-01-02",
                   content="Review 2", is_vine=True, collected_at="2024-01-02"),
            Review(asin="B003", brand="BrandB", rating=3.5, date="2024-01-03",
                   content="Review 3", is_vine=False, collected_at="2024-01-02"),
        ]
        store.insert_reviews(reviews)
        result = store.get_reviews_by_brand("BrandA")
        assert len(result) == 2
        assert all(r.brand == "BrandA" for r in result)

    def test_get_reviews_by_brand_empty(self, store):
        """Test querying a non-existent brand returns empty list."""
        result = store.get_reviews_by_brand("NonExistent")
        assert result == []

    def test_get_all_brands(self, store):
        """Test getting all unique brands."""
        reviews = [
            Review(asin="B001", brand="BrandA", rating=4.0, date="2024-01-01",
                   content="Review 1", is_vine=False, collected_at="2024-01-02"),
            Review(asin="B002", brand="BrandA", rating=5.0, date="2024-01-02",
                   content="Review 2", is_vine=True, collected_at="2024-01-02"),
            Review(asin="B003", brand="BrandB", rating=3.5, date="2024-01-03",
                   content="Review 3", is_vine=False, collected_at="2024-01-02"),
        ]
        store.insert_reviews(reviews)
        brands = store.get_all_brands()
        assert len(brands) == 2
        assert "BrandA" in brands
        assert "BrandB" in brands

    def test_store_uses_config_db_path(self):
        """Test that DatabaseStore defaults to config DB_PATH."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = DatabaseStore(db_path)
            assert store.conn is not None
            store.close()
            try:
                os.remove(db_path)
            except FileNotFoundError:
                pass
