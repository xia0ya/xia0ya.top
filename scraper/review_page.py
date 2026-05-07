"""Review page controller for scraping Amazon product reviews."""

import json
import os
import random
from typing import Optional

from playwright.sync_api import sync_playwright

from proxy.manager import ProxyManager
from rate_limiter import RateLimiter
from stealth.scripts import get_random_user_agent, get_stealth_script


class ReviewPageController:
    """Controls review page interactions with human-like behavior simulation."""

    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        cookies_path: Optional[str] = None,
    ) -> None:
        """Initialize the review page controller.

        Args:
            proxy_manager: Proxy manager for IP rotation. Defaults to ProxyManager().
            rate_limiter: Rate limiter for request throttling. Defaults to RateLimiter().
            cookies_path: Path to JSON file containing login cookies.
        """
        self.proxy_manager = proxy_manager or ProxyManager()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cookies_path = cookies_path or os.getenv("AMAZON_COOKIES", "cookies.json")
        self._cookies = None

    def _load_cookies(self) -> list:
        """Load cookies from JSON file."""
        if self._cookies is None:
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, 'r') as f:
                    raw_cookies = json.load(f)
                self._cookies = []
                for c in raw_cookies:
                    pc = {
                        'name': c['name'],
                        'value': c['value'],
                        'domain': c['domain'],
                        'path': c['path'],
                        'secure': c.get('secure', False),
                        'httpOnly': c.get('httpOnly', False),
                    }
                    same_site = c.get('sameSite', 'None')
                    if same_site not in ('Strict', 'Lax', 'None'):
                        same_site = 'None'
                    pc['sameSite'] = same_site
                    if 'expirationDate' in c:
                        pc['expires'] = c['expirationDate']
                    self._cookies.append(pc)
            else:
                self._cookies = []
        return self._cookies

    def _human_like_scroll(self, page) -> None:
        for _ in range(random.randint(3, 6)):
            scroll_distance = random.randint(300, 800)
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            page.wait_for_timeout(random.uniform(0.5, 1.5))

    def _human_like_move(self, page) -> None:
        x = random.randint(100, 800)
        y = random.randint(200, 600)
        page.mouse.move(x, y)
        page.wait_for_timeout(random.uniform(0.2, 0.8))

    def check_captcha(self, page) -> bool:
        """检测验证码.

        Returns:
            True 表示检测到验证码
        """
        try:
            captcha_indicators = [
                "captcha",
                "Enter the characters you see below",
                " Type the characters you see",
            ]
            page_text = page.content()
            for indicator in captcha_indicators:
                if indicator.lower() in page_text.lower():
                    return True
            return False
        except Exception as e:
            print(f"Warning: CAPTCHA check failed: {e}")
            return False

    def open_review_page(self, asin: str) -> Optional[dict]:
        """Open a product's review page.

        Returns:
            Dictionary with 'page' object, or None if fails.

        Note:
            Caller MUST call close_browser() to release resources.
        """
        cookies = self._load_cookies()

        user_agent = get_random_user_agent()
        viewport_width = random.randint(1280, 1920)
        viewport_height = random.randint(720, 1080)

        p = sync_playwright().start()
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        proxy = self.proxy_manager.get_proxy()
        context_options = {
            "viewport": {"width": viewport_width, "height": viewport_height},
            "user_agent": user_agent,
            "locale": random.choice(["en-US", "en-GB", "en"]),
        }
        if proxy:
            context_options["proxy"] = proxy

        context = browser.new_context(**context_options)
        context.add_init_script(get_stealth_script())

        if cookies:
            try:
                context.add_cookies(cookies)
            except Exception as e:
                print(f"Warning: Could not add cookies: {e}")

        page = context.new_page()
        review_url = f"https://www.amazon.com/product-reviews/{asin}/"
        page.goto(review_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        return {
            "playwright": p,
            "browser": browser,
            "context": context,
            "page": page,
            "asin": asin,
        }

    def close_browser(self, result: dict) -> None:
        """Close browser and playwright instance from open_review_page result."""
        if result.get("context"):
            result["context"].close()
        if result.get("browser"):
            result["browser"].close()
        if result.get("playwright"):
            result["playwright"].stop()

    def load_more_reviews(self, page, max_pages: int = 100) -> None:
        for i in range(max_pages):
            try:
                # 滚动到底部分页栏
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

                # 记录点击前的评论数
                before_count = page.evaluate("document.querySelectorAll('[data-hook=\"review\"]').length")

                # 查找分页栏中的 "Show X more reviews" 链接
                show_more_link = page.locator("#cm_cr-pagination_bar a[data-hook='show-more-button']")

                if show_more_link.count() > 0:
                    # 点击链接
                    show_more_link.first.click()
                    page.wait_for_timeout(3000)

                    # 记录点击后的评论数
                    after_count = page.evaluate("document.querySelectorAll('[data-hook=\"review\"]').length")
                    self.rate_limiter.sync_wait()
                    print(f"  -> 加载第 {i+1} 页... (评论数: {before_count} -> {after_count})")

                    # 如果评论数没有增加，说明没有更多了
                    if before_count >= after_count:
                        print(f"  -> 已加载所有评论 (共 {i+1} 页)")
                        break
                else:
                    # 没有更多按钮，结束
                    final_count = page.evaluate("document.querySelectorAll('[data-hook=\"review\"]').length")
                    print(f"  -> 已加载所有评论 (共 {i+1} 页, {final_count} 条)")
                    break

            except Exception as e:
                print(f"Error loading more reviews: {e}")
                continue
