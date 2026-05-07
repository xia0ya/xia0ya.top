import threading
from typing import Optional

import customtkinter as ctk

from .config_panel import ConfigPanel
from .link_input import LinkInput
from .log_view import LogView
from .progress_view import ProgressView
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter
from scraper.review_extractor import ReviewExtractor
from scraper.review_page import ReviewPageController


class ScraperApp(ctk.CTk):
    """Amazon 评论采集器主窗口"""

    def __init__(self):
        super().__init__()
        self.title("Amazon 评论采集器")
        self.geometry("700x750")

        # 状态
        self._scraping = False
        self._stop_flag = False
        self._review_count = 0
        self._completed_links = 0

        # 组件
        self.link_input = LinkInput(self)
        self.link_input.pack(fill="x", padx=10, pady=(10, 5))

        self.config_panel = ConfigPanel(self)
        self.config_panel.pack(fill="x", padx=10, pady=5)

        # 按钮行
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.start_btn = ctk.CTkButton(
            btn_frame, text="开始采集", command=self._start_scraping, width=100
        )
        self.start_btn.pack(side="left")

        self.stop_btn = ctk.CTkButton(
            btn_frame, text="停止", command=self._stop_scraping, width=100, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(5, 0))

        self.progress_view = ProgressView(self)
        self.progress_view.pack(fill="x", padx=10, pady=5)

        self.log_view = LogView(self, height=200)
        self.log_view.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    def _start_scraping(self) -> None:
        links = self.link_input.get_links()
        if not links:
            self.log_view.append_log("错误: 请先解析链接")
            return

        self._scraping = True
        self._stop_flag = False
        self._review_count = 0
        self._completed_links = 0

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.log_view.append_log(f"开始采集 {len(links)} 个链接...")

        thread = threading.Thread(target=self._scraping_worker, args=(links,), daemon=True)
        thread.start()

    def _stop_scraping(self) -> None:
        self._stop_flag = True
        self.log_view.append_log("正在停止...")

    def _scraping_worker(self, links: list) -> None:
        proxy_mode = self.config_panel.get_proxy_mode()
        manual_proxy = self.config_panel.get_manual_proxy()
        min_delay = self.config_panel.get_min_delay()
        max_delay = self.config_panel.get_max_delay()
        cookie_path = self.config_panel.get_cookie_path()

        proxy_mgr = ProxyManager(mode=proxy_mode, manual_proxy=manual_proxy)
        rate_limiter = RateLimiter(min_delay=min_delay, max_delay=max_delay)
        controller = ReviewPageController(proxy_manager=proxy_mgr, cookies_path=cookie_path)
        extractor = ReviewExtractor()

        total = len(links)

        for i, link in enumerate(links):
            if self._stop_flag:
                self.log_view.append_log("采集已停止")
                break

            self.log_view.append_log(f"[{i+1}/{total}] 正在采集: {link.asin}")

            try:
                result = controller.open_review_page(link.asin)
                if result is None:
                    self.log_view.append_log(f"  -> 页面打开失败")
                    continue

                try:
                    page = result["page"]
                    if controller.check_captcha(page):
                        self.log_view.append_log(f"  -> 检测到验证码")
                        continue

                    controller.load_more_reviews(page, max_pages=100)

                    reviews = extractor.extract(page)
                    count = len(reviews)
                    self._review_count += count
                    self.log_view.append_log(f"  -> 提取到 {count} 条评论")

                finally:
                    controller.close_browser(result)

            except Exception as e:
                self.log_view.append_log(f"  -> 错误: {e}")

            self._completed_links = i + 1
            self._update_progress()

            rate_limiter.sync_wait()

        self._scraping = False
        self._update_progress()

        self.after(0, self._on_scraping_complete)

    def _update_progress(self) -> None:
        links = self.link_input.get_links()
        total = len(links)
        self.progress_view.update(self._completed_links, total, self._review_count)

    def _on_scraping_complete(self) -> None:
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.log_view.append_log(f"采集完成! 共获取 {self._review_count} 条评论")
