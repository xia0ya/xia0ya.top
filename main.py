"""Main entry point for Amazon scraper.

Integrates all modules to:
1. Scrape product list from Amazon Best Sellers
2. Collect negative reviews for each product
3. Store reviews in SQLite database
4. Generate brand statistics summary
"""

import csv
import sys
from datetime import datetime

from config import config
from database.store import DatabaseStore, Review
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter
from scraper.product_list import ProductListScraper
from scraper.review_extractor import ReviewExtractor
from scraper.review_page import ReviewPageController


def scrape_and_store_reviews(
    products: list,
    proxy_manager: ProxyManager,
    rate_limiter: RateLimiter,
    db_store: DatabaseStore,
) -> None:
    """Scrape negative reviews for each product and store in database.

    Args:
        products: List of Product objects to process.
        proxy_manager: Proxy manager instance.
        rate_limiter: Rate limiter instance.
        db_store: Database store instance.
    """
    review_controller = ReviewPageController(
        proxy_manager=proxy_manager,
        rate_limiter=rate_limiter,
    )
    review_extractor = ReviewExtractor()
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = len(products)
    for idx, product in enumerate(products, start=1):
        print(f"[{idx}/{total}] Processing ASIN={product.asin} | {product.title[:50]}...")

        try:
            rate_limiter.sync_wait()

            result = review_controller.open_review_page(product.url)
            if result is None:
                print(f"  -> Failed to open review page, skipping")
                continue

            browser = result["browser"]
            page = result["page"]

            try:
                review_controller.load_more_reviews(page, max_pages=10)

                negative_reviews = review_extractor.extract_negative_reviews(page)

                if negative_reviews:
                    reviews = [
                        Review(
                            asin=product.asin,
                            brand=product.brand or "Unknown",
                            rating=r.rating,
                            date=r.date,
                            content=r.content,
                            is_vine=r.is_vine,
                            collected_at=collected_at,
                        )
                        for r in negative_reviews
                    ]
                    db_store.insert_reviews(reviews)
                    print(f"  -> Extracted {len(negative_reviews)} negative reviews")
                else:
                    print(f"  -> No negative reviews found")

            finally:
                browser.close()

        except Exception as e:
            print(f"  -> Error processing product: {e}")
            continue

    print(f"\nReview collection complete.")


def save_products_csv(products: list, filepath: str = "products.csv") -> None:
    """Save product list to CSV file.

    Args:
        products: List of Product objects.
        filepath: Output CSV path.
    """
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ASIN", "Title", "Brand", "URL"])
        for p in products:
            writer.writerow([p.asin, p.title, p.brand or "", p.url])
    print(f"Product list saved to {filepath} ({len(products)} products)")


def generate_brand_summary(db_store: DatabaseStore, filepath: str = "brand_summary.txt") -> None:
    """Generate brand statistics summary from collected reviews.

    Args:
        db_store: Database store with review data.
        filepath: Output summary file path.
    """
    brands = db_store.get_all_brands()

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Brand Summary Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 60}\n\n")

        for brand in brands:
            reviews = db_store.get_reviews_by_brand(brand)
            f.write(f"Brand: {brand}\n")
            f.write(f"  Total negative reviews: {len(reviews)}\n")
            if reviews:
                avg_rating = sum(r.rating for r in reviews) / len(reviews)
                f.write(f"  Average rating: {avg_rating:.2f}\n")
                vine_count = sum(1 for r in reviews if r.is_vine)
                f.write(f"  Vine reviews: {vine_count}\n")
            f.write("\n")

    print(f"Brand summary saved to {filepath}")


def main() -> None:
    """Run the full Amazon scraper pipeline."""
    print("=" * 60)
    print("Amazon Scraper Pipeline")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Initialize components
    print("\n[Step 1] Initializing components...")
    proxy_manager = ProxyManager()
    rate_limiter = RateLimiter()
    db_store = DatabaseStore()
    print("  ProxyManager, RateLimiter, DatabaseStore initialized.")

    # 2. Scrape product list
    print("\n[Step 2] Scraping product list...")
    scraper = ProductListScraper(
        proxy_manager=proxy_manager,
        rate_limiter=rate_limiter,
    )
    products = scraper.scrape(config.BASE_URL, max_products=config.MAX_PRODUCTS)
    print(f"  -> Collected {len(products)} products")

    if not products:
        print("ERROR: No products collected, aborting.")
        db_store.close()
        sys.exit(1)

    save_products_csv(products)

    # 3. Scrape and store negative reviews
    print("\n[Step 3] Scraping negative reviews...")
    scrape_and_store_reviews(products, proxy_manager, rate_limiter, db_store)

    # 4. Generate brand summary
    print("\n[Step 4] Generating brand summary...")
    generate_brand_summary(db_store)

    db_store.close()

    print("\n" + "=" * 60)
    print("Pipeline complete")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
