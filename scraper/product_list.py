"""Product list scraper for Amazon."""

import random
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import sync_playwright

from config import config
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter


@dataclass
class Product:
    """Represents an Amazon product."""

    asin: str
    title: str
    brand: Optional[str]
    url: str

    def __post_init__(self):
        """Validate product data after initialization."""
        if not self.asin:
            raise ValueError("ASIN is required")
        if not self.url:
            raise ValueError("URL is required")


# Anti-detection stealth scripts
STEALTH_JS = '''
Object.defineProperty(navigator, 'webdriver', { get: () => false });
delete window.cdc_adoQpoasnfaapdkofahrepdgpnhkgeL;
delete window.__webdriver_evaluate;
delete window.__webdriver_script_function;
delete window.__webdriver_script_func;
delete window.__webdriver_script_fn;
'''


class ProductListScraper:
    """Scrapes product lists from Amazon search results and Best Sellers pages."""

    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        """Initialize the product list scraper.

        Args:
            proxy_manager: Proxy manager for IP rotation. Defaults to ProxyManager().
            rate_limiter: Rate limiter for request throttling. Defaults to RateLimiter().
        """
        self.proxy_manager = proxy_manager or ProxyManager()
        self.rate_limiter = rate_limiter or RateLimiter()

    def _human_like_scroll(self, page) -> None:
        """Simulate human-like scrolling to trigger lazy loading.

        Args:
            page: Playwright Page object.
        """
        for _ in range(random.randint(2, 4)):
            scroll_distance = random.randint(300, 700)
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            page.wait_for_timeout(random.uniform(0.3, 1.0))

    def _extract_products_from_page(self, page) -> list[Product]:
        """Extract product data from the current page.

        Args:
            page: Playwright Page object.

        Returns:
            List of Product objects.
        """
        products = []

        # Amazon product cards are typically in [data-asin] containers
        # Common selectors for product list items
        product_selectors = [
            "[data-asin]",
            "[data-component-type='s-search-result']",
            ".s-result-item",
        ]

        product_elements = None
        for selector in product_selectors:
            elements = page.locator(selector).all()
            if elements:
                product_elements = elements
                break

        if not product_elements:
            return products

        for element in product_elements:
            try:
                asin = element.get_attribute("data-asin")
                if not asin or asin == "PFAKE":
                    continue

                # Get product URL
                url = f"https://www.amazon.com/dp/{asin}"

                # Get title - try multiple selectors
                title = (
                    element.locator("a span").first.text_content()
                    or element.locator("a").first.get_attribute("title")
                    or element.locator("span[class*='a-text-normal']").first.text_content()
                    or ""
                ).strip()

                # Skip if title is empty or looks like price info
                if not title or title.startswith('('):
                    continue

                # Get brand - simplified
                brand_elem = element.locator("[class*='a-color-secondary']").first
                if brand_elem.count() > 0:
                    brand = brand_elem.text_content().strip()
                    if brand.startswith('('):
                        brand = None
                    elif brand:
                        brand = brand.replace("Visit the ", "").replace(" Store", "").strip()
                else:
                    brand = None

                if title:
                    products.append(Product(
                        asin=asin,
                        title=title,
                        brand=brand,
                        url=url,
                    ))
            except Exception:
                continue

        return products

    def scrape(self, url: str = None, max_products: int = 50) -> list[Product]:
        """Scrape product list from a given URL.

        Args:
            url: Amazon URL to scrape. Defaults to config.BASE_URL.
            max_products: Maximum number of products to collect. Defaults to 50.

        Returns:
            List of Product objects.
        """
        url = url or config.BASE_URL
        all_products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--lang=en-US",
                ],
            )

            proxy = self.proxy_manager.get_proxy()
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                "locale": "en-US",
            }
            if proxy:
                context_options["proxy"] = proxy

            context = browser.new_context(**context_options)
            context.add_init_script(STEALTH_JS)
            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)  # Wait for content to load

                # Extract initial products
                products = self._extract_products_from_page(page)
                all_products.extend(products)
            finally:
                context.close()
                browser.close()

        # Limit to max_products
        return all_products[:max_products]
