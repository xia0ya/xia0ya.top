"""Database storage module for Amazon scraper."""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from config import config


@dataclass
class Review:
    """Review data class."""

    asin: str
    brand: str
    rating: float
    date: str
    content: str
    is_vine: bool
    collected_at: str


class DatabaseStore:
    """Database store for reviews."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Optional path to database file. Defaults to config.DB_PATH.
        """
        self.db_path = db_path or config.DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Create reviews table and indexes."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                brand TEXT NOT NULL,
                rating REAL,
                date TEXT,
                content TEXT,
                is_vine INTEGER DEFAULT 0,
                collected_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand ON reviews(brand)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_asin ON reviews(asin)")
        self.conn.commit()

    def insert_review(self, review: Review) -> None:
        """Insert a single review.

        Args:
            review: Review instance to insert.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO reviews (asin, brand, rating, date, content, is_vine, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review.asin,
                review.brand,
                review.rating,
                review.date,
                review.content,
                1 if review.is_vine else 0,
                review.collected_at,
            ),
        )
        self.conn.commit()

    def insert_reviews(self, reviews: List[Review]) -> None:
        """Bulk insert reviews using executemany.

        Args:
            reviews: List of Review instances to insert.
        """
        cursor = self.conn.cursor()
        data = [
            (
                r.asin,
                r.brand,
                r.rating,
                r.date,
                r.content,
                1 if r.is_vine else 0,
                r.collected_at,
            )
            for r in reviews
        ]
        cursor.executemany(
            """
            INSERT INTO reviews (asin, brand, rating, date, content, is_vine, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        self.conn.commit()

    def get_reviews_by_brand(self, brand: str) -> List[Review]:
        """Get reviews by brand name.

        Args:
            brand: Brand name to search for.

        Returns:
            List of Review instances matching the brand.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT asin, brand, rating, date, content, is_vine, collected_at FROM reviews WHERE brand=?",
            (brand,),
        )
        rows = cursor.fetchall()
        return [
            Review(
                asin=row[0],
                brand=row[1],
                rating=row[2],
                date=row[3],
                content=row[4],
                is_vine=bool(row[5]),
                collected_at=row[6],
            )
            for row in rows
        ]

    def get_all_brands(self) -> List[str]:
        """Get all unique brand names.

        Returns:
            List of unique brand names.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT brand FROM reviews ORDER BY brand")
        return [row[0] for row in cursor.fetchall()]

    def get_all_reviews(self) -> list:
        """获取所有评论"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT asin, brand, rating, date, content, is_vine, collected_at FROM reviews ORDER BY id DESC")
        rows = cursor.fetchall()
        return [
            Review(
                asin=row[0],
                brand=row[1],
                rating=row[2],
                date=row[3],
                content=row[4],
                is_vine=bool(row[5]),
                collected_at=row[6],
            )
            for row in rows
        ]

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
