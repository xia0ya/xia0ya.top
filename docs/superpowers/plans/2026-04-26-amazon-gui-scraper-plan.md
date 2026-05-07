# Amazon GUI 采集器实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为不懂编程的用户实现一款桌面工具，通过图形界面采集亚马逊商品评论数据

**Architecture:**
- GUI 层: CustomTkinter 实现现代化界面
- 核心层: 复用现有爬虫引擎，增强反爬
- 支持双代理模式（系统代理/手动输入）+ 断点续采
- 打包: PyInstaller 单 exe

**Tech Stack:** Python 3.10+, CustomTkinter, Playwright, PyInstaller, SQLite

---

## 文件结构

```
amazon-scraper/
├── gui/                         # 新建
│   ├── __init__.py
│   ├── app.py                   # 主窗口
│   ├── link_input.py            # 链接输入组件
│   ├── config_panel.py           # 配置面板
│   ├── progress_view.py          # 进度显示
│   └── log_view.py              # 日志组件
├── stealth/                     # 新建
│   ├── __init__.py
│   └── scripts.py               # 反爬脚本
├── core/                        # 新建（核心功能封装）
│   ├── __init__.py
│   ├── link_parser.py           # 链接解析
│   ├── progress_tracker.py       # 断点续采
│   └── scraper_engine.py        # 爬虫引擎
├── scraper/
│   ├── review_page.py           # 修改: 集成 stealth
│   └── review_extractor.py      # 修改: 提取所有评论
├── proxy/
│   └── manager.py               # 修改: 双代理模式
├── database/
│   └── store.py                 # 已有，修改 brand 字段
├── gui_main.py                  # 新建: GUI 入口
└── requirements.txt             # 修改: 添加 customtkinter
```

---

## Task 1: 创建 stealth 模块（反爬增强）

**Files:**
- Create: `stealth/__init__.py`
- Create: `stealth/scripts.py`

- [ ] **Step 1: 创建 stealth/__init__.py**

```python
"""Stealth anti-detection module."""

from .scripts import get_stealth_script, get_random_user_agent

__all__ = ["get_stealth_script", "get_random_user_agent"]
```

- [ ] **Step 2: 创建 stealth/scripts.py（UA 池 + 增强 stealth 脚本）**

```python
"""Anti-detection scripts for Playwright."""

import random

# Chrome User-Agent 池（10+ 个真实 UA）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

# 基础 stealth 脚本（注入到浏览器上下文）
BASE_STEALTH_SCRIPT = '''
Object.defineProperty(navigator, 'webdriver', { get: () => false });
delete window.cdc_adoQpoasnfaapdkofahrepdgpnhkgeL;
delete window.__webdriver_evaluate;
delete window.__webdriver_script_function;
delete window.__webdriver_script_func;
delete window.__webdriver_script_fn;
'''

# 增强 stealth 脚本（覆盖更多指纹）
ENHANCED_STEALTH_SCRIPT = '''
// 隐藏 webdriver
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// 移除自动化标识
delete window.cdc_adoQpoasnfaapdkofahrepdgpnhkgeL;
delete window.__webdriver_evaluate;
delete window.__webdriver_script_function;
delete window.__webdriver_script_func;
delete window.__webdriver_script_fn;

// 模拟真实的 plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', description: '', filename: 'internal-nacl-plugin' }
    ]
});

// 模拟 languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en', 'zh-CN', 'zh']
});

// 模拟 permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// WebGL 指纹处理
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Open Source Technology Center';
    if (parameter === 37446) return 'Mesa DRI Intel(R) Ivybridge Mobile';
    return getParameter.apply(this, arguments);
};
'''

def get_random_user_agent() -> str:
    """返回随机 User-Agent"""
    return random.choice(USER_AGENTS)

def get_stealth_script() -> str:
    """返回增强的 stealth 脚本"""
    return ENHANCED_STEALTH_SCRIPT

def get_base_stealth_script() -> str:
    """返回基础 stealth 脚本"""
    return BASE_STEALTH_SCRIPT
```

- [ ] **Step 3: 提交**

```bash
git add stealth/__init__.py stealth/scripts.py
git commit -m "feat: add stealth module with random UA and enhanced fingerprint hiding"
```

---

## Task 2: 改进 ProxyManager（双代理模式）

**Files:**
- Modify: `proxy/manager.py:1-111`
- Create: `proxy/system_proxy.py`（读取系统代理）

- [ ] **Step 1: 创建 proxy/system_proxy.py**

```python
"""System proxy detection for Windows."""

import os
import subprocess
from typing import Optional

def get_system_proxy() -> Optional[dict]:
    """读取 Windows 系统代理设置.

    Returns:
        {
            "server": "http://ip:port",
            "username": "xxx",  # 可选
            "password": "xxx"    # 可选
        }
        或 None（未启用代理）
    """
    try:
        # 使用 reg query 获取 IE 代理设置
        result = subprocess.run(
            ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings',
             '/v', 'ProxyEnable'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )

        if '0x0' in result.stdout:
            return None  # 代理未启用

        # 获取代理服务器地址
        result2 = subprocess.run(
            ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings',
             '/v', 'ProxyServer'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )

        # 解析格式: proxy.server.com:8080 或 ip=xxx.xxx.xxx.xxx;port=xxxx
        import re
        match = re.search(r'ProxyServer\s+REG_SZ\s+(.+)', result2.stdout)
        if match:
            server = match.group(1).strip()
            # 处理格式: ip:port
            if ':' in server:
                return {"server": f"http://{server}"}
            return None

        return None
    except Exception:
        return None

def is_proxy_enabled() -> bool:
    """检查系统代理是否启用"""
    proxy = get_system_proxy()
    return proxy is not None
```

- [ ] **Step 2: 修改 proxy/manager.py（添加双模式支持）**

```python
"""Proxy manager module for handling proxy rotation and configuration."""

import os
from enum import Enum
from typing import List, Optional

from config import config
from .system_proxy import get_system_proxy


class ProxyMode(Enum):
    """代理模式枚举"""
    SYSTEM = "system"      # 系统代理
    MANUAL = "manual"     # 手动输入
    NONE = "none"         # 无代理


class ProxyManager:
    """Manages proxy list and rotation for Playwright browser automation."""

    def __init__(self, mode: ProxyMode = ProxyMode.SYSTEM, manual_proxy: Optional[str] = None) -> None:
        """初始化 ProxyManager.

        Args:
            mode: 代理模式（系统代理/手动输入/无代理）
            manual_proxy: 手动代理字符串，格式 ip:port:user:pass 或 ip:port
        """
        self.mode = mode
        self.manual_proxy = manual_proxy
        self._proxies: List[dict] = []
        self._current_index: int = 0
        self._system_proxy: Optional[dict] = None

        if mode == ProxyMode.SYSTEM:
            self._system_proxy = get_system_proxy()

    def _load_manual_proxy(self, proxy_str: str) -> Optional[dict]:
        """解析手动代理字符串.

        Args:
            proxy_str: 格式 ip:port:user:pass 或 ip:port

        Returns:
            代理字典或 None
        """
        parts = proxy_str.strip().split(":")

        if len(parts) == 4:
            return {
                "server": f"http://{parts[0]}:{parts[1]}",
                "username": parts[2],
                "password": parts[3],
            }
        elif len(parts) == 2:
            return {
                "server": f"http://{parts[0]}:{parts[1]}",
                "username": "",
                "password": "",
            }
        return None

    def get_proxy(self) -> Optional[object]:
        """获取当前代理（Playwright 格式）.

        Returns:
            _PlaywrightProxy 对象，或 None（无代理模式）
        """
        if self.mode == ProxyMode.NONE:
            return None

        if self.mode == ProxyMode.SYSTEM:
            if self._system_proxy is None:
                return None
            return _PlaywrightProxy(
                server=self._system_proxy["server"],
                username=self._system_proxy.get("username", ""),
                password=self._system_proxy.get("password", ""),
            )

        if self.mode == ProxyMode.MANUAL:
            if not self._proxies:
                if self.manual_proxy:
                    proxy = self._load_manual_proxy(self.manual_proxy)
                    if proxy:
                        self._proxies.append(proxy)
            if not self._proxies:
                return None
            proxy_dict = self._proxies[self._current_index]
            return _PlaywrightProxy(
                server=proxy_dict["server"],
                username=proxy_dict.get("username", ""),
                password=proxy_dict.get("password", ""),
            )

        return None

    def rotate(self) -> Optional[object]:
        """轮换到下一个代理（仅手动模式有效）"""
        if self.mode != ProxyMode.MANUAL:
            return self.get_proxy()

        if not self._proxies:
            return None

        self._current_index = (self._current_index + 1) % len(self._proxies)
        return self.get_proxy()

    def set_manual_proxy(self, proxy_str: str) -> None:
        """设置手动代理"""
        self.manual_proxy = proxy_str
        self._proxies = []
        self._current_index = 0
        proxy = self._load_manual_proxy(proxy_str)
        if proxy:
            self._proxies.append(proxy)


class _PlaywrightProxy:
    """Playwright 代理配置"""

    def __init__(self, server: str, username: str, password: str) -> None:
        self.server = server
        self.username = username
        self.password = password

    def __repr__(self) -> str:
        return f"_PlaywrightProxy(server={self.server!r}, username={self.username!r})"
```

- [ ] **Step 3: 提交**

```bash
git add proxy/system_proxy.py proxy/manager.py
git commit -m "feat: add dual proxy mode (system/manual) to ProxyManager"
```

---

## Task 3: 创建 core 模块（链接解析 + 断点续采）

**Files:**
- Create: `core/__init__.py`
- Create: `core/link_parser.py`
- Create: `core/progress_tracker.py`

- [ ] **Step 1: 创建 core/__init__.py**

```python
"""Core functionality modules."""

from .link_parser import LinkParser, ParsedLink
from .progress_tracker import ProgressTracker

__all__ = ["LinkParser", "ParsedLink", "ProgressTracker"]
```

- [ ] **Step 2: 创建 core/link_parser.py**

```python
"""Link parser for Amazon product and review URLs."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse


class LinkType(Enum):
    """链接类型枚举"""
    PRODUCT = "product"      # 商品页 /dp/ASIN
    REVIEW = "review"        # 评论页 /product-reviews/ASIN
    UNKNOWN = "unknown"      # 未知格式


@dataclass
class ParsedLink:
    """解析后的链接"""
    original: str          # 原始链接
    asin: str               # ASIN
    link_type: LinkType     # 类型
    review_url: str         # 评论页 URL（统一转换为评论页）


class LinkParser:
    """解析 Amazon 商品/评论链接"""

    # ASIN 正则: 10 位，以 B0 开头
    ASIN_PATTERN = r'(B0[A-Z0-9]{9})'

    @classmethod
    def extract_asin(cls, text: str) -> Optional[str]:
        """从文本中提取 ASIN"""
        match = re.search(cls.ASIN_PATTERN, text, re.IGNORECASE)
        return match.group(1) if match else None

    @classmethod
    def detect_link_type(cls, url: str) -> LinkType:
        """检测链接类型"""
        parsed = urlparse(url.lower()

        if '/product-reviews/' in parsed.path:
            return LinkType.REVIEW
        if '/dp/' in parsed.path or '/gp/product/' in parsed.path:
            return LinkType.PRODUCT

        # 如果 path 包含 ASIN 但不是标准格式，也当作商品页
        asin = cls.extract_asin(url)
        if asin:
            return LinkType.PRODUCT

        return LinkType.UNKNOWN

    @classmethod
    def to_review_url(cls, url: str) -> str:
        """将任意 Amazon 链接转换为评论页 URL"""
        asin = cls.extract_asin(url)
        if not asin:
            raise ValueError(f"无法从链接中提取 ASIN: {url}")
        return f"https://www.amazon.com/product-reviews/{asin}/"

    @classmethod
    def parse(cls, url: str) -> Optional[ParsedLink]:
        """解析链接.

        Args:
            url: Amazon 商品页或评论页 URL

        Returns:
            ParsedLink 对象，或 None（无法解析）
        """
        url = url.strip()

        asin = cls.extract_asin(url)
        if not asin:
            return None

        link_type = cls.detect_link_type(url)
        if link_type == LinkType.UNKNOWN:
            return None

        return ParsedLink(
            original=url,
            asin=asin,
            link_type=link_type,
            review_url=cls.to_review_url(url),
        )

    @classmethod
    def parse_multi(cls, text: str) -> List[ParsedLink]:
        """解析多行文本中的所有链接.

        Args:
            text: 多行文本，每行一个 URL 或混有其他内容

        Returns:
            解析成功的 ParsedLink 列表
        """
        results = []

        # 按行分割
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # 尝试提取 URL（可能在文本中间）
            asin = cls.extract_asin(line)
            if asin:
                # 尝试解析为完整 URL
                url = line
                if not url.startswith('http'):
                    url = f"https://www.amazon.com/dp/{asin}/"
                try:
                    parsed = cls.parse(url)
                    if parsed:
                        results.append(parsed)
                except ValueError:
                    pass

        # 去重（按 ASIN）
        seen = set()
        unique = []
        for p in results:
            if p.asin not in seen:
                seen.add(p.asin)
                unique.append(p)

        return unique

    @classmethod
    def parse_file(cls, filepath: str) -> List[ParsedLink]:
        """从文件读取并解析链接.

        Args:
            filepath: .txt 或 .csv 文件路径

        Returns:
            解析成功的 ParsedLink 列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls.parse_multi(content)
```

- [ ] **Step 3: 创建 core/progress_tracker.py**

```python
"""Progress tracker for resume support."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set


DEFAULT_PROGRESS_FILE = "progress.json"


@dataclass
class ProgressState:
    """进度状态"""
    total: int = 0
    completed: List[str] = field(default_factory=list)  # 已完成的 ASIN 列表
    last_updated: str = ""

    def mark_completed(self, asin: str) -> None:
        """标记一个 ASIN 为已完成"""
        if asin not in self.completed:
            self.completed.append(asin)
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def is_completed(self, asin: str) -> bool:
        """检查 ASIN 是否已完成"""
        return asin in self.completed

    def get_remaining(self, all_asins: List[str]) -> List[str]:
        """获取未完成的 ASIN 列表"""
        return [a for a in all_asins if a not in self.completed]

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "completed": self.completed,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressState":
        return cls(
            total=data.get("total", 0),
            completed=data.get("completed", []),
            last_updated=data.get("last_updated", ""),
        )


class ProgressTracker:
    """断点续采追踪器"""

    def __init__(self, filepath: str = DEFAULT_PROGRESS_FILE):
        self.filepath = filepath
        self.state = ProgressState()
        self._load()

    def _load(self) -> None:
        """从文件加载进度"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.state = ProgressState.from_dict(data)
            except (json.JSONDecodeError, IOError):
                self.state = ProgressState()

    def _save(self) -> None:
        """保存进度到文件"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)

    def init(self, total: int) -> None:
        """初始化进度（设置总数）"""
        self.state.total = total
        self.state.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save()

    def mark_completed(self, asin: str) -> None:
        """标记完成并保存"""
        self.state.mark_completed(asin)
        self._save()

    def is_completed(self, asin: str) -> bool:
        """检查是否已完成"""
        return self.state.is_completed(asin)

    def get_remaining(self, all_asins: List[str]) -> List[str]:
        """获取剩余未采集的 ASIN"""
        return self.state.get_remaining(all_asins)

    def get_completed_count(self) -> int:
        """获取已完成数量"""
        return len(self.state.completed)

    def get_total(self) -> int:
        """获取总数"""
        return self.state.total

    def reset(self) -> None:
        """重置进度"""
        self.state = ProgressState()
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
```

- [ ] **Step 4: 提交**

```bash
git add core/__init__.py core/link_parser.py core/progress_tracker.py
git commit -m "feat: add core module with link parser and progress tracker"
```

---

## Task 4: 修改 ReviewPageController（集成 stealth）

**Files:**
- Modify: `scraper/review_page.py:1-183`

- [ ] **Step 1: 备份并修改 scraper/review_page.py**

替换原来的 `STEALTH_JS` 为调用 stealth 模块:

```python
"""Review page controller for scraping Amazon product reviews."""

import json
import os
import random
from typing import Optional

from playwright.sync_api import sync_playwright

from core.link_parser import LinkParser, ParsedLink
from core.progress_tracker import ProgressTracker
from proxy.manager import ProxyManager, ProxyMode
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
        self.proxy_manager = proxy_manager or ProxyManager()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cookies_path = cookies_path or os.getenv("AMAZON_COOKIES", "cookies.json")
        self._cookies = None

    def _load_cookies(self) -> list:
        """Load cookies from JSON file."""
        # ... 保持原有代码 ...

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

    def open_review_page(self, asin: str) -> Optional[dict]:
        """Open a product's review page.

        Returns:
            Dictionary with 'page' object, or None if fails.
        """
        cookies = self._load_cookies()

        p = sync_playwright().start()

        # 随机 UA
        user_agent = get_random_user_agent()

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features",
            ],
        )

        proxy = self.proxy_manager.get_proxy()
        context_options = {
            "viewport": {"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
            "user_agent": user_agent,
            "locale": random.choice(["en-US", "en-GB", "en"]),
        }
        if proxy:
            context_options["proxy"] = {
                "server": proxy.server,
                "username": proxy.username if proxy.username else None,
                "password": proxy.password if proxy.password else None,
            }

        context = browser.new_context(**context_options)

        # 使用增强 stealth 脚本
        context.add_init_script(get_stealth_script())

        if cookies:
            try:
                context.add_cookies(cookies)
            except Exception as e:
                print(f"Warning: Could not add cookies: {e}")

        page = context.new_page()
        review_url = f"https://www.amazon.com/product-reviews/{asin}/"
        page.goto(review_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        return {
            "playwright": p,
            "browser": browser,
            "context": context,
            "page": page,
            "asin": asin,
        }

    def close_browser(self, result: dict) -> None:
        """Close browser and playwright instance."""
        # ... 保持原有代码 ...

    def load_more_reviews(self, page, max_pages: int = 100) -> None:
        # ... 保持原有代码（已有分页滚动逻辑）...

    def check_captcha(self, page) -> bool:
        """检测验证码.

        Returns:
            True 表示检测到验证码
        """
        try:
            # 亚马逊验证码特征
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
        except Exception:
            return False
```

- [ ] **Step 2: 提交**

```bash
git add scraper/review_page.py
git commit -m "feat: integrate stealth module and random UA into ReviewPageController"
```

---

## Task 5: 修改 ReviewExtractor（提取所有评论）

**Files:**
- Modify: `scraper/review_extractor.py:1-206`

- [ ] **Step 1: 添加 extract_all_reviews 方法（已有），添加 extract_reviews 方法**

在 `ReviewExtractor` 类中添加:

```python
def extract_reviews(self, page: Page, min_rating: Optional[float] = None) -> List[ExtractedReview]:
    """Extract reviews from the page, optionally filtered by rating.

    Args:
        page: Playwright Page object.
        min_rating: Minimum rating to include (None = include all).

    Returns:
        List of ExtractedReview objects.
    """
    reviews_data = page.evaluate("""
        () => {
            const reviews = [];
            const reviewEls = document.querySelectorAll('[data-hook="review"]');
            reviewEls.forEach(el => {
                let rating = null;
                const ratingEl = el.querySelector('[data-hook="review-star-rating"]');
                if (ratingEl) {
                    const match = ratingEl.textContent.match(/([\\d.]+)/);
                    if (match) rating = parseFloat(match[1]);
                }

                let date = '';
                const dateEl = el.querySelector('[data-hook="review-date"]');
                if (dateEl) date = dateEl.textContent;

                let content = '';
                const bodyEl = el.querySelector('[data-hook="review-body"]');
                if (bodyEl) content = bodyEl.innerText;

                const vineEl = el.querySelector('[data-hook="vine-badge"]');
                const isVine = vineEl !== null;

                if (rating !== null) {
                    reviews.push({ rating, date, content, is_vine: isVine });
                }
            });
            return reviews;
        }
    """)

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
```

- [ ] **Step 2: 提交**

```bash
git add scraper/review_extractor.py
git commit -m "feat: add extract_reviews with optional rating filter"
```

---

## Task 6: 创建 GUI 模块

**Files:**
- Create: `gui/__init__.py`
- Create: `gui/app.py`
- Create: `gui/link_input.py`
- Create: `gui/config_panel.py`
- Create: `gui/progress_view.py`
- Create: `gui/log_view.py`

- [ ] **Step 1: 创建 gui/__init__.py**

```python
"""GUI module for Amazon scraper."""

from .app import ScraperApp

__all__ = ["ScraperApp"]
```

- [ ] **Step 2: 创建 gui/log_view.py**

```python
"""Log view component for displaying scraping logs."""

import customtkinter as ctk
from datetime import datetime
from queue import Queue, Empty
from typing import Optional
import threading


class LogView(ctk.CTkTextbox):
    """Scrolling log textbox with thread-safe updates."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(state="disabled")
        self.log_queue: Queue = Queue()
        self._poll_log()

    def append_log(self, message: str) -> None:
        """添加日志（线程安全）"""
        self.log_queue.put(message)

    def _poll_log(self) -> None:
        """定期检查日志队列"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._add_text(msg)
        except Empty:
            pass
        self.after(100, self._poll_log)

    def _add_text(self, message: str) -> None:
        """实际添加文本到控件"""
        self.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.insert("end", f"[{timestamp}] {message}\n")
        self.see("end")
        self.configure(state="disabled")

    def clear(self) -> None:
        """清空日志"""
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")
```

- [ ] **Step 3: 创建 gui/progress_view.py**

```python
"""Progress view component."""

import customtkinter as ctk


class ProgressView(ctk.CTkFrame):
    """Progress display frame with link count, review count, and progress bar."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Link progress
        self.link_label = ctk.CTkLabel(self, text="链接: 0/0")
        self.link_label.pack(pady=(0, 5))

        # Review count
        self.review_label = ctk.CTkLabel(self, text="已采集: 0 条评论")
        self.review_label.pack(pady=(0, 5))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)

        # Percentage
        self.percent_label = ctk.CTkLabel(self, text="0%")
        self.percent_label.pack()

    def update(self, completed_links: int, total_links: int, review_count: int) -> None:
        """更新进度显示"""
        self.link_label.configure(text=f"链接: {completed_links}/{total_links}")
        self.review_label.configure(text=f"已采集: {review_count} 条评论")

        if total_links > 0:
            percent = completed_links / total_links
            self.progress_bar.set(percent)
            self.percent_label.configure(text=f"{int(percent * 100)}%")
        else:
            self.progress_bar.set(0)
            self.percent_label.configure(text="0%")

    def reset(self) -> None:
        """重置进度"""
        self.update(0, 0, 0)
```

- [ ] **Step 4: 创建 gui/config_panel.py**

```python
"""Configuration panel component."""

import customtkinter as ctk
from typing import Callable, Optional
from proxy.manager import ProxyMode


class ConfigPanel(ctk.CTkFrame):
    """Configuration panel with proxy settings and request interval."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Proxy mode
        self.proxy_mode_label = ctk.CTkLabel(self, text="代理模式:")
        self.proxy_mode_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.proxy_mode_var = ctk.StringVar(value="system")

        self.system_proxy_radio = ctk.CTkRadioButton(
            self, text="系统代理 (VPN)",
            variable=self.proxy_mode_var, value="system"
        )
        self.system_proxy_radio.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        self.manual_proxy_radio = ctk.CTkRadioButton(
            self, text="手动输入",
            variable=self.proxy_mode_var, value="manual"
        )
        self.manual_proxy_radio.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # Manual proxy input
        self.manual_proxy_label = ctk.CTkLabel(self, text="代理地址:")
        self.manual_proxy_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.manual_proxy_entry = ctk.CTkEntry(self, width=250, placeholder_text="ip:port:user:pass")
        self.manual_proxy_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Request interval
        self.interval_label = ctk.CTkLabel(self, text="请求间隔:")
        self.interval_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.min_delay_entry = ctk.CTkEntry(self, width=60, placeholder_text="8")
        self.min_delay_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        self.interval_separator = ctk.CTkLabel(self, text=" - ")
        self.interval_separator.grid(row=2, column=2, sticky="w", padx=0, pady=5)

        self.max_delay_entry = ctk.CTkEntry(self, width=60, placeholder_text="15")
        self.max_delay_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)

        self.seconds_label = ctk.CTkLabel(self, text="秒")
        self.seconds_label.grid(row=2, column=4, sticky="w", padx=0, pady=5)

        # Cookie file
        self.cookie_label = ctk.CTkLabel(self, text="Cookie文件:")
        self.cookie_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

        self.cookie_entry = ctk.CTkEntry(self, width=200, placeholder_text="cookies.json")
        self.cookie_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.cookie_entry.insert(0, "cookies.json")

        self.cookie_browse_btn = ctk.CTkButton(
            self, text="浏览", width=60,
            command=self._browse_cookie
        )
        self.cookie_browse_btn.grid(row=3, column=2, sticky="w", padx=5, pady=5)

    def _browse_cookie(self) -> None:
        """打开文件选择对话框"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="选择 Cookie 文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.cookie_entry.delete(0, "end")
            self.cookie_entry.insert(0, filename)

    def get_proxy_mode(self) -> ProxyMode:
        """获取代理模式"""
        mode = self.proxy_mode_var.get()
        if mode == "manual":
            return ProxyMode.MANUAL
        return ProxyMode.SYSTEM

    def get_manual_proxy(self) -> Optional[str]:
        """获取手动代理字符串"""
        proxy = self.manual_proxy_entry.get().strip()
        return proxy if proxy else None

    def get_min_delay(self) -> float:
        try:
            return float(self.min_delay_entry.get())
        except ValueError:
            return 8.0

    def get_max_delay(self) -> float:
        try:
            return float(self.max_delay_entry.get())
        except ValueError:
            return 15.0

    def get_cookie_path(self) -> str:
        return self.cookie_entry.get().strip() or "cookies.json"
```

- [ ] **Step 5: 创建 gui/link_input.py**

```python
"""Link input component."""

import customtkinter as ctk
from tkinter import filedialog
from core.link_parser import LinkParser, ParsedLink


class LinkInput(ctk.CTkFrame):
    """Link input frame with text area and file import."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Label
        self.label = ctk.CTkLabel(self, text="链接输入 (每行一个):")
        self.label.pack(anchor="w", padx=5, pady=(5, 0))

        # Text area
        self.textbox = ctk.CTkTextbox(self, height=120)
        self.textbox.pack(fill="x", padx=5, pady=5)

        # Buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=5, pady=(0, 5))

        self.import_btn = ctk.CTkButton(
            self.btn_frame, text="导入文件",
            command=self._import_file,
            width=100
        )
        self.import_btn.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self.btn_frame, text="清空",
            command=self._clear,
            width=60
        )
        self.clear_btn.pack(side="left", padx=(5, 0))

        self.parse_btn = ctk.CTkButton(
            self.btn_frame, text="解析链接",
            command=self._parse,
            width=80
        )
        self.parse_btn.pack(side="left", padx=(5, 0))

        # Status label
        self.status_label = ctk.CTkLabel(
            self, text="",
            text_color="gray"
        )
        self.status_label.pack(anchor="w", padx=5, pady=(0, 5))

        self._parsed_links: list[ParsedLink] = []

    def _import_file(self) -> None:
        """导入文件"""
        filename = filedialog.askopenfilename(
            title="选择链接文件",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.textbox.delete("1.0", "end")
                self.textbox.insert("1.0", content)
                self._parse()
            except Exception as e:
                self.status_label.configure(text=f"读取文件失败: {e}", text_color="red")

    def _clear(self) -> None:
        """清空输入"""
        self.textbox.delete("1.0", "end")
        self.status_label.configure(text="")
        self._parsed_links = []

    def _parse(self) -> None:
        """解析链接"""
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            self.status_label.configure(text="请输入链接", text_color="orange")
            return

        links = LinkParser.parse_multi(text)
        self._parsed_links = links

        if links:
            asins = [l.asin for l in links]
            self.status_label.configure(
                text=f"解析成功: {len(links)} 个链接 ({', '.join(asins[:3])}{'...' if len(asins) > 3 else ''})",
                text_color="green"
            )
        else:
            self.status_label.configure(text="未解析到有效链接", text_color="red")

    def get_links(self) -> list[ParsedLink]:
        """获取解析后的链接"""
        return self._parsed_links

    def get_text(self) -> str:
        """获取原始文本"""
        return self.textbox.get("1.0", "end").strip()
```

- [ ] **Step 6: 创建 gui/app.py（主窗口）**

```python
"""Main application window."""

import customtkinter as ctk
import threading
from datetime import datetime
from typing import Optional

from core.link_parser import LinkParser, ParsedLink
from core.progress_tracker import ProgressTracker
from database.store import DatabaseStore, Review
from proxy.manager import ProxyManager, ProxyMode
from rate_limiter import RateLimiter
from scraper.review_page import ReviewPageController
from scraper.review_extractor import ReviewExtractor

from .config_panel import ConfigPanel
from .link_input import LinkInput
from .log_view import LogView
from .progress_view import ProgressView


class ScraperApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("Amazon 评论采集器")
        self.geometry("700x700")

        # State
        self._scraping = False
        self._stop_flag = False
        self._scraper_thread: Optional[threading.Thread] = None
        self._db_store: Optional[DatabaseStore] = None
        self._review_count = 0

        # Layout
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Title
        title = ctk.CTkLabel(self, text="Amazon 评论采集器", font=("Arial", 18, "bold"))
        title.pack(pady=(10, 5))

        # Link input
        self.link_input = LinkInput(self)
        self.link_input.pack(fill="x", padx=20, pady=(5, 5))

        # Config panel
        self.config_panel = ConfigPanel(self)
        self.config_panel.pack(fill="x", padx=20, pady=(5, 5))

        # Control buttons
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=20, pady=(5, 5))

        self.start_btn = ctk.CTkButton(
            self.control_frame, text="开始采集",
            command=self._start_scraping,
            fg_color="green"
        )
        self.start_btn.pack(side="left", padx=(0, 5))

        self.stop_btn = ctk.CTkButton(
            self.control_frame, text="停止采集",
            command=self._stop_scraping,
            state="disabled",
            fg_color="red"
        )
        self.stop_btn.pack(side="left")

        # Progress view
        self.progress_view = ProgressView(self)
        self.progress_view.pack(fill="x", padx=20, pady=(5, 5))

        # Log view
        log_label = ctk.CTkLabel(self, text="日志:")
        log_label.pack(anchor="w", padx=20)

        self.log_view = LogView(self, height=200)
        self.log_view.pack(fill="both", expand=True, padx=20, pady=(5, 10))

    def _start_scraping(self) -> None:
        """Start scraping in a background thread."""
        links = self.link_input.get_links()
        if not links:
            self.log_view.append_log("错误: 请先输入或导入有效链接")
            return

        if self._scraping:
            self.log_view.append_log("警告: 已经在采集中")
            return

        self._scraping = True
        self._stop_flag = False
        self._review_count = 0
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self._scraper_thread = threading.Thread(target=self._scraping_worker, args=(links,))
        self._scraper_thread.start()

    def _stop_scraping(self) -> None:
        """Signal to stop scraping."""
        self._stop_flag = True
        self.log_view.append_log("正在停止...")

    def _scraping_worker(self, links: list[ParsedLink]) -> None:
        """Background scraping worker."""
        try:
            self.log_view.append_log(f"开始采集 {len(links)} 个链接...")

            # Setup
            proxy_mode = self.config_panel.get_proxy_mode()
            manual_proxy = self.config_panel.get_manual_proxy()
            proxy_manager = ProxyManager(mode=proxy_mode, manual_proxy=manual_proxy)

            min_delay = self.config_panel.get_min_delay()
            max_delay = self.config_panel.get_max_delay()
            rate_limiter = RateLimiter(min_delay=min_delay, max_delay=max_delay)

            cookie_path = self.config_panel.get_cookie_path()
            review_controller = ReviewPageController(
                proxy_manager=proxy_manager,
                rate_limiter=rate_limiter,
                cookies_path=cookie_path,
            )
            review_extractor = ReviewExtractor()

            self._db_store = DatabaseStore()
            tracker = ProgressTracker()
            tracker.init(len(links))

            collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Process each link
            completed = 0
            for link in links:
                if self._stop_flag:
                    self.log_view.append_log("采集已停止")
                    break

                asin = link.asin
                self.log_view.append_log(f"处理: {asin}")

                # Check if already completed (resume)
                if tracker.is_completed(asin):
                    self.log_view.append_log(f"  已完成，跳过: {asin}")
                    completed += 1
                    self.progress_view.update(completed, len(links), self._review_count)
                    continue

                try:
                    rate_limiter.sync_wait()

                    result = review_controller.open_review_page(asin)
                    if result is None:
                        self.log_view.append_log(f"  打开页面失败")
                        continue

                    try:
                        # Check captcha
                        if review_controller.check_captcha(result["page"]):
                            self.log_view.append_log(f"  ⚠️ 检测到验证码，请手动处理后重试")
                            break

                        # Load more reviews
                        review_controller.load_more_reviews(result["page"], max_pages=100)

                        # Extract all reviews
                        reviews = review_extractor.extract_reviews(result["page"])

                        if reviews:
                            db_reviews = [
                                Review(
                                    asin=asin,
                                    brand="",
                                    rating=r.rating,
                                    date=r.date,
                                    content=r.content,
                                    is_vine=r.is_vine,
                                    collected_at=collected_at,
                                )
                                for r in reviews
                            ]
                            self._db_store.insert_reviews(db_reviews)
                            self._review_count += len(reviews)
                            self.log_view.append_log(f"  提取 {len(reviews)} 条评论")

                        tracker.mark_completed(asin)
                        completed += 1
                        self.progress_view.update(completed, len(links), self._review_count)

                    finally:
                        review_controller.close_browser(result)

                except Exception as e:
                    self.log_view.append_log(f"  错误: {e}")
                    continue

            # Done
            self._scraping = False
            self._db_store.close()
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

            if self._stop_flag:
                self.log_view.append_log("采集已停止（部分完成）")
            else:
                self.log_view.append_log(f"✅ 采集完成！共 {self._review_count} 条评论")

        except Exception as e:
            self._scraping = False
            self.log_view.append_log(f"错误: {e}")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def run(self) -> None:
        """Run the application."""
        self.mainloop()
```

- [ ] **Step 7: 提交**

```bash
git add gui/__init__.py gui/app.py gui/link_input.py gui/config_panel.py gui/progress_view.py gui/log_view.py
git commit -m "feat: add GUI module with CustomTkinter"
```

---

## Task 7: 创建 GUI 入口和打包配置

**Files:**
- Create: `gui_main.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 创建 gui_main.py**

```python
"""GUI entry point for Amazon scraper."""

import sys
import os

# 确保项目根目录在 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import ScraperApp

if __name__ == "__main__":
    app = ScraperApp()
    app.run()
```

- [ ] **Step 2: 更新 requirements.txt**

```
playwright
customtkinter
pyinstaller
```

- [ ] **Step 3: 创建 PyInstaller spec 文件 (amazon_scraper.spec)**

```spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('cookies.json', '.'),
    ],
    hiddenimports=[
        'playwright',
        'customtkinter',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AmazonScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- [ ] **Step 4: 添加打包脚本 build.bat**

```bat
@echo off
echo Building Amazon Scraper...

pip install -r requirements.txt
playwright install chromium
pyinstaller amazon_scraper.spec --clean

echo Build complete! Executable is in dist/ folder.
pause
```

- [ ] **Step 5: 提交**

```bash
git add gui_main.py requirements.txt amazon_scraper.spec build.bat
git commit -m "feat: add GUI entry point and PyInstaller config"
```

---

## Task 8: 整体测试

**Files:**
- Test: 完整流程

- [ ] **Step 1: 运行 GUI 测试**

```bash
python gui_main.py
```

预期: GUI 窗口打开，可以输入链接

- [ ] **Step 2: 测试链接解析**

```bash
python -c "
from core.link_parser import LinkParser
links = LinkParser.parse_multi('''https://www.amazon.com/dp/B0FMNCV88Q
https://www.amazon.com/product-reviews/B0XXXXXXX/''')
print([l.asin for l in links])
"
```

预期: 输出 ['B0FMNCV88Q', 'B0XXXXXXX']

- [ ] **Step 3: 测试 stealth 模块**

```bash
python -c "
from stealth.scripts import get_random_user_agent, get_stealth_script
print('UA:', get_random_user_agent()[:50])
print('Script length:', len(get_stealth_script()))
"
```

预期: 打印 UA（不同）和脚本长度

- [ ] **Step 4: 提交**

```bash
git commit -m "test: add and verify all modules work together"
```

---

## 实现顺序

1. **Task 1** - stealth 模块（基础依赖）
2. **Task 2** - ProxyManager（依赖 stealth）
3. **Task 3** - core 模块（独立）
4. **Task 4** - ReviewPageController（集成 stealth）
5. **Task 5** - ReviewExtractor
6. **Task 6** - GUI 模块
7. **Task 7** - 入口和打包
8. **Task 8** - 整体测试

---

## 风险与注意事项

1. **Playwright 打包** - 需要在 spec 中正确配置，包含 chromium
2. **验证码** - 遇到验证码会暂停，需要用户手动处理
3. **Cookie 过期** - 登录态有时效，需要定期更新
4. **反爬检测** - stealth 不能 100% 隐藏，VPN 是必要的

---

**Plan complete.** 两个执行选项：

**1. Subagent-Driven (recommended)** - 每个 Task 由独立 subagent 执行，我在中途 review

**2. Inline Execution** - 在这个 session 内批量执行，定期 checkpoint 让你 review

选择哪个？
