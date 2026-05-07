"""Tests for product list scraper."""

import unittest

from scraper.product_list import Product, ProductListScraper


class TestProduct(unittest.TestCase):
    """Test suite for Product dataclass."""

    def test_product_creation_with_required_fields(self):
        """Test creating a Product with required fields."""
        product = Product(
            asin="B08N5WRWNW",
            title="Electric Toothbrush",
            brand="Oral-B",
            url="https://www.amazon.com/dp/B08N5WRWNW",
        )
        self.assertEqual(product.asin, "B08N5WRWNW")
        self.assertEqual(product.title, "Electric Toothbrush")
        self.assertEqual(product.brand, "Oral-B")
        self.assertEqual(product.url, "https://www.amazon.com/dp/B08N5WRWNW")

    def test_product_creation_without_brand(self):
        """Test creating a Product without brand."""
        product = Product(
            asin="B08N5WRWNW",
            title="Electric Toothbrush",
            brand=None,
            url="https://www.amazon.com/dp/B08N5WRWNW",
        )
        self.assertIsNone(product.brand)

    def test_product_creation_without_asin_raises(self):
        """Test that creating a Product without ASIN raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Product(
                asin="",
                title="Electric Toothbrush",
                brand="Oral-B",
                url="https://www.amazon.com/dp/B08N5WRWNW",
            )
        self.assertEqual(str(context.exception), "ASIN is required")

    def test_product_creation_without_url_raises(self):
        """Test that creating a Product without URL raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Product(
                asin="B08N5WRWNW",
                title="Electric Toothbrush",
                brand="Oral-B",
                url="",
            )
        self.assertEqual(str(context.exception), "URL is required")

    def test_product_dataclass_is_frozen_false(self):
        """Test that Product is not frozen (mutable)."""
        product = Product(
            asin="B08N5WRWNW",
            title="Electric Toothbrush",
            brand=None,
            url="https://www.amazon.com/dp/B08N5WRWNW",
        )
        # Should be able to modify brand
        product.brand = "NewBrand"
        self.assertEqual(product.brand, "NewBrand")


class TestProductListScraper(unittest.TestCase):
    """Test suite for ProductListScraper class."""

    def test_scraper_initialization(self):
        """Test that scraper initializes with default managers."""
        scraper = ProductListScraper()
        self.assertIsNotNone(scraper.proxy_manager)
        self.assertIsNotNone(scraper.rate_limiter)

    def test_scraper_initialization_with_custom_managers(self):
        """Test that scraper accepts custom managers."""
        from proxy.manager import ProxyManager
        from rate_limiter import RateLimiter

        custom_proxy = ProxyManager()
        custom_limiter = RateLimiter()
        scraper = ProductListScraper(
            proxy_manager=custom_proxy,
            rate_limiter=custom_limiter,
        )
        self.assertIs(scraper.proxy_manager, custom_proxy)
        self.assertIs(scraper.rate_limiter, custom_limiter)

    def test_human_like_scroll_exists(self):
        """Test that _human_like_scroll method exists."""
        scraper = ProductListScraper()
        self.assertTrue(hasattr(scraper, "_human_like_scroll"))
        self.assertTrue(callable(scraper._human_like_scroll))

    def test_extract_products_from_page_exists(self):
        """Test that _extract_products_from_page method exists."""
        scraper = ProductListScraper()
        self.assertTrue(hasattr(scraper, "_extract_products_from_page"))
        self.assertTrue(callable(scraper._extract_products_from_page))

    def test_scrape_method_exists(self):
        """Test that scrape method exists."""
        scraper = ProductListScraper()
        self.assertTrue(hasattr(scraper, "scrape"))
        self.assertTrue(callable(scraper.scrape))


if __name__ == "__main__":
    unittest.main()
