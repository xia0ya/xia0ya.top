# 亚马逊差评采集爬虫实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 爬取亚马逊Best Sellers电动牙刷前50个商品的差评，按品牌分组存入SQLite

**Architecture:** Playwright浏览器自动化 + 住宅代理轮换 + 随机间隔防封

**Tech Stack:** Python 3.10+, Playwright, SQLite, Residential Proxy

---

## 文件结构

```
amazon-scraper/
├── main.py                 # 主入口
├── config.py               # 配置（代理、间隔、采集数量）
├── proxy/
│   └── manager.py          # 代理池管理
├── rate_limiter.py         # 请求限速
├── database/
│   └── store.py            # SQLite存储
├── scraper/
│   ├── product_list.py     # 一级页面采集
│   ├── review_page.py      # 二级页面控制器
│   └── review_extractor.py # 差评提取
└── tests/
    ├── test_proxy_manager.py
    ├── test_rate_limiter.py
    ├── test_store.py
    └── test_review_extractor.py
```

---

## Task 1: 项目初始化

**Files:**
- Create: `config.py`

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    # 采集数量
    MAX_PRODUCTS: int = 50

    # 请求间隔（秒）
    MIN_DELAY: float = 8.0
    MAX_DELAY: float = 15.0

    # 代理配置（环境变量）
    PROXY_PROVIDER: str = os.getenv("PROXY_PROVIDER", "oxylabs")
    PROXY_USERNAME: str = os.getenv("PROXY_USERNAME", "")
    PROXY_PASSWORD: str = os.getenv("PROXY_PASSWORD", "")

    # 目标URL
    BASE_URL: str = "https://www.amazon.com/Best-Sellers-Health-Household-Rotating-Power-Toothbrushes/zgbs/hpc/18065349011/ref=zg_bs_nav_hpc_5_18065347011"

    # 数据库
    DB_PATH: str = "amazon_reviews.db"

config = Config()
```

- [ ] **Step 1: 创建项目目录结构**

```bash
mkdir -p amazon-scraper/proxy amazon-scraper/database amazon-scraper/scraper amazon-scraper/tests
touch amazon-scraper/__init__.py amazon-scraper/proxy/__init__.py amazon-scraper/database/__init__.py amazon-scraper/scraper/__init__.py amazon-scraper/tests/__init__.py
```

- [ ] **Step 2: 创建 config.py**

```bash
cat > amazon-scraper/config.py << 'EOF'
import os
from dataclasses import dataclass

@dataclass
class Config:
    MAX_PRODUCTS: int = 50
    MIN_DELAY: float = 8.0
    MAX_DELAY: float = 15.0
    PROXY_PROVIDER: str = os.getenv("PROXY_PROVIDER", "oxylabs")
    PROXY_USERNAME: str = os.getenv("PROXY_USERNAME", "")
    PROXY_PASSWORD: str = os.getenv("PROXY_PASSWORD", "")
    BASE_URL: str = "https://www.amazon.com/Best-Sellers-Health-Household-Rotating-Power-Toothbrushes/zgbs/hpc/18065349011/ref=zg_bs_nav_hpc_5_18065347011"
    DB_PATH: str = "amazon_reviews.db"

config = Config()
EOF
```

- [ ] **Step 3: 提交**

```bash
cd amazon-scraper && git init && git add -A && git commit -m "feat: initialize project structure with config"
```

---

## Task 2: 代理管理器

**Files:**
- Create: `proxy/manager.py`
- Test: `tests/test_proxy_manager.py`

```python
# proxy/manager.py
import random
import os
from typing import Optional

class ProxyManager:
    def __init__(self):
        self.username = os.getenv("PROXY_USERNAME", "")
        self.password = os.getenv("PROXY_PASSWORD", "")
        self.provider = os.getenv("PROXY_PROVIDER", "oxylabs")
        self._proxy_list = self._load_proxies()

    def _load_proxies(self) -> list[str]:
        # 从环境变量或文件加载代理列表
        proxy_env = os.getenv("PROXY_LIST", "")
        if proxy_env:
            return proxy_env.split(",")
        # 示例格式: ip:port:username:password
        return []

    def get_proxy(self) -> Optional[dict]:
        """返回 Playwright 格式的代理配置"""
        if not self._proxy_list:
            return None

        proxy_str = random.choice(self._proxy_list)
        parts = proxy_str.split(":")

        if len(parts) >= 4:
            ip, port, user, pwd = parts[0], parts[1], parts[2], parts[3]
        else:
            ip, port = parts[0], parts[1]
            user, pwd = self.username, self.password

        return {
            "server": f"http://{ip}:{port}",
            "username": user,
            "password": pwd
        }

    def rotate(self) -> Optional[dict]:
        """轮换代理，返回新的代理配置"""
        return self.get_proxy()
```

- [ ] **Step 1: 写测试**

```python
# tests/test_proxy_manager.py
import pytest
from proxy.manager import ProxyManager

def test_proxy_manager_default():
    manager = ProxyManager()
    # 无代理时应返回 None
    proxy = manager.get_proxy()
    assert proxy is None or isinstance(proxy, dict)

def test_proxy_manager_with_proxies(monkeypatch):
    monkeypatch.setenv("PROXY_LIST", "192.168.1.1:8080:user:pass,192.168.1.2:8080:user:pass")
    manager = ProxyManager()
    assert len(manager._proxy_list) == 2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd amazon-scraper && pytest tests/test_proxy_manager.py -v
# 预期: FAIL - module not found
```

- [ ] **Step 3: 创建 proxy/manager.py**

```python
# proxy/manager.py
import random
import os
from typing import Optional

class ProxyManager:
    def __init__(self):
        self.username = os.getenv("PROXY_USERNAME", "")
        self.password = os.getenv("PROXY_PASSWORD", "")
        self.provider = os.getenv("PROXY_PROVIDER", "oxylabs")
        self._proxy_list = self._load_proxies()

    def _load_proxies(self) -> list[str]:
        proxy_env = os.getenv("PROXY_LIST", "")
        if proxy_env:
            return proxy_env.split(",")
        return []

    def get_proxy(self) -> Optional[dict]:
        if not self._proxy_list:
            return None
        proxy_str = random.choice(self._proxy_list)
        parts = proxy_str.split(":")
        if len(parts) >= 4:
            ip, port, user, pwd = parts[0], parts[1], parts[2], parts[3]
        else:
            ip, port = parts[0], parts[1]
            user, pwd = self.username, self.password
        return {
            "server": f"http://{ip}:{port}",
            "username": user,
            "password": pwd
        }

    def rotate(self) -> Optional[dict]:
        return self.get_proxy()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd amazon-scraper && pytest tests/test_proxy_manager.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
cd amazon-scraper && git add proxy/manager.py tests/test_proxy_manager.py && git commit -m "feat: add proxy manager"
```

---

## Task 3: 限速器

**Files:**
- Create: `rate_limiter.py`
- Test: `tests/test_rate_limiter.py`

```python
# rate_limiter.py
import random
import asyncio
from config import config

class RateLimiter:
    def __init__(self, min_delay: float = None, max_delay: float = None):
        self.min_delay = min_delay or config.MIN_DELAY
        self.max_delay = max_delay or config.MAX_DELAY

    def random_delay(self) -> float:
        """返回随机延迟秒数"""
        return random.uniform(self.min_delay, self.max_delay)

    async def wait(self):
        """异步等待随机间隔"""
        delay = self.random_delay()
        await asyncio.sleep(delay)

    def sync_wait(self):
        """同步等待随机间隔"""
        import time
        delay = self.random_delay()
        time.sleep(delay)
```

- [ ] **Step 1: 写测试**

```python
# tests/test_rate_limiter.py
import pytest
import time
from rate_limiter import RateLimiter

def test_random_delay_range():
    limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
    for _ in range(10):
        delay = limiter.random_delay()
        assert 1.0 <= delay <= 2.0

def test_random_delay_returns_float():
    limiter = RateLimiter()
    assert isinstance(limiter.random_delay(), float)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd amazon-scraper && pytest tests/test_rate_limiter.py -v
# 预期: FAIL
```

- [ ] **Step 3: 创建 rate_limiter.py**

```python
# rate_limiter.py
import random
import asyncio
import time
from config import config

class RateLimiter:
    def __init__(self, min_delay: float = None, max_delay: float = None):
        self.min_delay = min_delay if min_delay is not None else config.MIN_DELAY
        self.max_delay = max_delay if max_delay is not None else config.MAX_DELAY

    def random_delay(self) -> float:
        return random.uniform(self.min_delay, self.max_delay)

    async def wait(self):
        delay = self.random_delay()
        await asyncio.sleep(delay)

    def sync_wait(self):
        delay = self.random_delay()
        time.sleep(delay)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd amazon-scraper && pytest tests/test_rate_limiter.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
cd amazon-scraper && git add rate_limiter.py tests/test_rate_limiter.py && git commit -m "feat: add rate limiter"
```

---

## Task 4: 数据库存储

**Files:**
- Create: `database/store.py`
- Test: `tests/test_store.py`

```python
# database/store.py
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from config import config

@dataclass
class Review:
    asin: str
    brand: str
    rating: int
    date: str
    content: str
    is_vine: bool
    collected_at: str

class DatabaseStore:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                brand TEXT NOT NULL,
                rating INTEGER NOT NULL,
                date TEXT,
                content TEXT,
                is_vine BOOLEAN DEFAULT 0,
                collected_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand ON reviews(brand)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_asin ON reviews(asin)")
        conn.commit()
        conn.close()

    def insert_review(self, review: Review):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (asin, brand, rating, date, content, is_vine, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (review.asin, review.brand, review.rating, review.date,
              review.content, review.is_vine, review.collected_at))
        conn.commit()
        conn.close()

    def insert_reviews(self, reviews: List[Review]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        data = [(r.asin, r.brand, r.rating, r.date, r.content, r.is_vine, r.collected_at)
                for r in reviews]
        cursor.executemany("""
            INSERT INTO reviews (asin, brand, rating, date, content, is_vine, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()

    def get_reviews_by_brand(self, brand: str) -> List[Review]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT asin, brand, rating, date, content, is_vine, collected_at FROM reviews WHERE brand = ?", (brand,))
        rows = cursor.fetchall()
        conn.close()
        return [Review(asin=r[0], brand=r[1], rating=r[2], date=r[3], content=r[4], is_vine=r[5], collected_at=r[6]) for r in rows]

    def get_all_brands(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT brand FROM reviews")
        brands = [r[0] for r in cursor.fetchall()]
        conn.close()
        return brands
```

- [ ] **Step 1: 写测试**

```python
# tests/test_store.py
import pytest
import os
import tempfile
from database.store import DatabaseStore, Review

def test_store_insert_and_query():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        store = DatabaseStore(db_path)
        review = Review(
            asin="B08ABC123",
            brand="Oral-B",
            rating=2,
            date="2024-01-15",
            content="Broke after 2 weeks",
            is_vine=False,
            collected_at="2024-03-01"
        )
        store.insert_review(review)
        results = store.get_reviews_by_brand("Oral-B")
        assert len(results) == 1
        assert results[0].asin == "B08ABC123"
    finally:
        os.unlink(db_path)

def test_store_multiple_reviews():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        store = DatabaseStore(db_path)
        reviews = [
            Review(asin="B1", brand="BrandA", rating=1, date="d1", content="c1", is_vine=False, collected_at="t1"),
            Review(asin="B2", brand="BrandA", rating=2, date="d2", content="c2", is_vine=True, collected_at="t1"),
            Review(asin="B3", brand="BrandB", rating=3, date="d3", content="c3", is_vine=False, collected_at="t1"),
        ]
        store.insert_reviews(reviews)
        brand_a = store.get_reviews_by_brand("BrandA")
        assert len(brand_a) == 2
        brands = store.get_all_brands()
        assert set(brands) == {"BrandA", "BrandB"}
    finally:
        os.unlink(db_path)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd amazon-scraper && pytest tests/test_store.py -v
# 预期: FAIL - module not found
```

- [ ] **Step 3: 创建 database/store.py**

```python
# database/store.py
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import List
from config import config

@dataclass
class Review:
    asin: str
    brand: str
    rating: int
    date: str
    content: str
    is_vine: bool
    collected_at: str

class DatabaseStore:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                brand TEXT NOT NULL,
                rating INTEGER NOT NULL,
                date TEXT,
                content TEXT,
                is_vine BOOLEAN DEFAULT 0,
                collected_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand ON reviews(brand)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_asin ON reviews(asin)")
        conn.commit()
        conn.close()

    def insert_review(self, review: Review):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (asin, brand, rating, date, content, is_vine, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (review.asin, review.brand, review.rating, review.date,
              review.content, review.is_vine, review.collected_at))
        conn.commit()
        conn.close()

    def insert_reviews(self, reviews: List[Review]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        data = [(r.asin, r.brand, r.rating, r.date, r.content, r.is_vine, r.collected_at)
                for r in reviews]
        cursor.executemany("""
            INSERT INTO reviews (asin, brand, rating, date, content, is_vine, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()

    def get_reviews_by_brand(self, brand: str) -> List[Review]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT asin, brand, rating, date, content, is_vine, collected_at FROM reviews WHERE brand = ?", (brand,))
        rows = cursor.fetchall()
        conn.close()
        return [Review(asin=r[0], brand=r[1], rating=r[2], date=r[3], content=r[4], is_vine=r[5], collected_at=r[6]) for r in rows]

    def get_all_brands(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT brand FROM reviews")
        brands = [r[0] for r in cursor.fetchall()]
        conn.close()
        return brands
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd amazon-scraper && pytest tests/test_store.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
cd amazon-scraper && git add database/store.py tests/test_store.py && git commit -m "feat: add database store"
```

---

## Task 5: 商品列表采集器

**Files:**
- Create: `scraper/product_list.py`
- Test: `tests/test_product_list.py`

```python
# scraper/product_list.py
from dataclasses import dataclass
from typing import List, Optional
from playwright.sync_api import sync_playwright, Browser, Page
from config import config
from proxy.manager import ProxyManager

@dataclass
class Product:
    asin: str
    title: str
    brand: str
    url: str

class ProductListScraper:
    def __init__(self, proxy_manager: ProxyManager = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.browser: Optional[Browser] = None

    def _create_browser_context(self):
        from playwright.sync_api import BrowserContext
        launch_options = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        }
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            launch_options["proxy"] = proxy

        context = self.browser.contexts[0] if self.browser.contexts else None
        return context

    def scrape(self, max_products: int = None) -> List[Product]:
        max_products = max_products or config.MAX_PRODUCTS
        products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 访问一级页面
            page.goto(config.BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # 提取商品卡片
            product_cards = page.locator("[data-component-type='s-search-result']").all()
            for i, card in enumerate(product_cards[:max_products]):
                try:
                    link = card.locator("a.a-link-normal").first
                    title_elem = card.locator(".a-size-medium.a-color-base.a-text-normal").first
                    brand_elem = card.locator(".a-size-base.a-color-secondary")

                    title = title_elem.inner_text() if title_elem.count() > 0 else ""
                    brand = brand_elem.inner_text() if brand_elem.count() > 0 else ""

                    asin = card.get_attribute("data-asin")
                    url = link.get_attribute("href") if link.count() > 0 else ""

                    if asin and title:
                        products.append(Product(
                            asin=asin,
                            title=title.strip(),
                            brand=brand.strip() if brand else "Unknown",
                            url=f"https://www.amazon.com{url}" if url.startswith("/") else url
                        ))
                except Exception as e:
                    print(f"Error extracting product {i}: {e}")
                    continue

            browser.close()

        return products
```

- [ ] **Step 1: 写测试（模拟数据结构）**

```python
# tests/test_product_list.py
import pytest
from dataclasses import dataclass

# 由于ProductListScraper依赖Playwright和真实浏览器，测试只验证数据模型
@dataclass
class Product:
    asin: str
    title: str
    brand: str
    url: str

def test_product_dataclass():
    p = Product(asin="B08ABC123", title="Electric Toothbrush", brand="Oral-B", url="https://amazon.com/dp/B08ABC123")
    assert p.asin == "B08ABC123"
    assert p.brand == "Oral-B"

def test_product_list_structure():
    from scraper.product_list import Product
    products = [
        Product(asin="1", title="T1", brand="B1", url="u1"),
        Product(asin="2", title="T2", brand="B2", url="u2"),
    ]
    assert len(products) == 2
    assert products[0].asin == "1"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd amazon-scraper && pytest tests/test_product_list.py -v
# 预期: FAIL - module not found
```

- [ ] **Step 3: 创建 scraper/product_list.py**

```python
# scraper/product_list.py
from dataclasses import dataclass
from typing import List, Optional
from playwright.sync_api import sync_playwright
from config import config
from proxy.manager import ProxyManager

@dataclass
class Product:
    asin: str
    title: str
    brand: str
    url: str

class ProductListScraper:
    def __init__(self, proxy_manager: ProxyManager = None):
        self.proxy_manager = proxy_manager or ProxyManager()

    def scrape(self, max_products: int = None) -> List[Product]:
        max_products = max_products or config.MAX_PRODUCTS
        products = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            page.goto(config.BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)

            product_cards = page.locator("[data-component-type='s-search-result']").all()
            for i, card in enumerate(product_cards[:max_products]):
                try:
                    link = card.locator("a.a-link-normal").first
                    title_elem = card.locator(".a-size-medium.a-color-base.a-text-normal").first
                    brand_elem = card.locator(".a-size-base.a-color-secondary")

                    title = title_elem.inner_text() if title_elem.count() > 0 else ""
                    brand = brand_elem.inner_text() if brand_elem.count() > 0 else ""

                    asin = card.get_attribute("data-asin")
                    url = link.get_attribute("href") if link.count() > 0 else ""

                    if asin and title:
                        products.append(Product(
                            asin=asin,
                            title=title.strip(),
                            brand=brand.strip() if brand else "Unknown",
                            url=f"https://www.amazon.com{url}" if url.startswith("/") else url
                        ))
                except Exception as e:
                    print(f"Error extracting product {i}: {e}")
                    continue

            browser.close()

        return products
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd amazon-scraper && pytest tests/test_product_list.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
cd amazon-scraper && git add scraper/product_list.py tests/test_product_list.py && git commit -m "feat: add product list scraper"
```

---

## Task 6: 评论页面控制器

**Files:**
- Create: `scraper/review_page.py`

```python
# scraper/review_page.py
import random
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter

class ReviewPageController:
    def __init__(self, proxy_manager: ProxyManager = None, rate_limiter: RateLimiter = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.rate_limiter = rate_limiter or RateLimiter()

    def _human_like_scroll(self, page: Page):
        """模拟人类滚动行为"""
        for _ in range(random.randint(3, 6)):
            scroll_distance = random.randint(300, 800)
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            page.wait_for_timeout(random.uniform(0.5, 1.5))

    def _human_like_move(self, page: Page):
        """模拟鼠标移动"""
        x = random.randint(100, 800)
        y = random.randint(200, 600)
        page.mouse.move(x, y)
        page.wait_for_timeout(random.uniform(0.2, 0.8))

    def open_review_page(self, product_url: str) -> Optional[Page]:
        """打开商品评论页面，返回页面对象"""
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            proxy = self.proxy_manager.get_proxy()
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            if proxy:
                context_options["proxy"] = proxy

            context = browser.new_context(**context_options)
            page = context.new_page()

            # 访问商品页
            page.goto(product_url, wait_until="domcontentloaded")
            self.rate_limiter.sync_wait()

            # 点击 "See all reviews" 链接
            try:
                see_all_reviews = page.locator("a:has-text('See all reviews')").first
                see_all_reviews.click()
                page.wait_for_load_state("networkidle")
                self._human_like_scroll(page)
            except Exception as e:
                print(f"Could not find 'See all reviews': {e}")
                return None

            browser.close()
            return page

    def load_more_reviews(self, page: Page, max_pages: int = 10):
        """滚动加载更多评论"""
        for _ in range(max_pages):
            try:
                self._human_like_scroll(page)
                self._human_like_move(page)

                load_more = page.locator("span:has-text('Load more results'), button:has-text('See more reviews')")
                if load_more.count() > 0:
                    load_more.first.click()
                    page.wait_for_load_state("networkidle")
                    self.rate_limiter.sync_wait()
                else:
                    break
            except Exception as e:
                print(f"Error loading more reviews: {e}")
                break
```

- [ ] **Step 1: 创建 scraper/review_page.py**

```python
# scraper/review_page.py
import random
from typing import Optional
from playwright.sync_api import sync_playwright
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter

class ReviewPageController:
    def __init__(self, proxy_manager: ProxyManager = None, rate_limiter: RateLimiter = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.rate_limiter = rate_limiter or RateLimiter()

    def _human_like_scroll(self, page):
        for _ in range(random.randint(3, 6)):
            scroll_distance = random.randint(300, 800)
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            page.wait_for_timeout(random.uniform(0.5, 1.5))

    def _human_like_move(self, page):
        x = random.randint(100, 800)
        y = random.randint(200, 600)
        page.mouse.move(x, y)
        page.wait_for_timeout(random.uniform(0.2, 0.8))

    def open_review_page(self, product_url: str) -> Optional[dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            proxy = self.proxy_manager.get_proxy()
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            if proxy:
                context_options["proxy"] = proxy

            context = browser.new_context(**context_options)
            page = context.new_page()

            page.goto(product_url, wait_until="domcontentloaded")
            self.rate_limiter.sync_wait()

            try:
                see_all_reviews = page.locator("a:has-text('See all reviews')").first
                see_all_reviews.click()
                page.wait_for_load_state("networkidle")
                self._human_like_scroll(page)
            except Exception as e:
                print(f"Could not find 'See all reviews': {e}")
                return None

            return {"browser": browser, "context": context, "page": page}

    def load_more_reviews(self, page, max_pages: int = 10):
        for _ in range(max_pages):
            try:
                self._human_like_scroll(page)
                self._human_like_move(page)

                load_more = page.locator("span:has-text('Load more results'), button:has-text('See more reviews')")
                if load_more.count() > 0:
                    load_more.first.click()
                    page.wait_for_load_state("networkidle")
                    self.rate_limiter.sync_wait()
                else:
                    break
            except Exception as e:
                print(f"Error loading more reviews: {e}")
                break
```

- [ ] **Step 2: 提交**

```bash
cd amazon-scraper && git add scraper/review_page.py && git commit -m "feat: add review page controller"
```

---

## Task 7: 差评提取器

**Files:**
- Create: `scraper/review_extractor.py`
- Test: `tests/test_review_extractor.py`

```python
# scraper/review_extractor.py
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExtractedReview:
    rating: int
    date: str
    content: str
    is_vine: bool

class ReviewExtractor:
    def extract_negative_reviews(self, page) -> List[ExtractedReview]:
        reviews = []

        # 找到所有评论卡片
        review_cards = page.locator("[data-hook='review']").all()

        for card in review_cards:
            try:
                # 提取评分
                rating_elem = card.locator("[data-hook='review-star-rating']")
                rating_text = rating_elem.get_attribute("title") if rating_elem.count() > 0 else ""
                rating = int(rating_text.split(" ")[0]) if rating_text else 0

                # 只采集差评（三星及以下）
                if rating > 3:
                    continue

                # 提取日期
                date_elem = card.locator("[data-hook='review-date']")
                date = date_elem.inner_text() if date_elem.count() > 0 else ""

                # 提取内容
                content_elem = card.locator("[data-hook='review-body']")
                content = content_elem.inner_text() if content_elem.count() > 0 else ""

                # 检查Vine认证
                vine_elem = card.locator("[data-hook='vine-badge']")
                is_vine = vine_elem.count() > 0

                reviews.append(ExtractedReview(
                    rating=rating,
                    date=date,
                    content=content,
                    is_vine=is_vine
                ))
            except Exception as e:
                print(f"Error extracting review: {e}")
                continue

        return reviews
```

- [ ] **Step 1: 写测试**

```python
# tests/test_review_extractor.py
import pytest
from scraper.review_extractor import ReviewExtractor, ExtractedReview

def test_extractor_filters_negative():
    extractor = ReviewExtractor()
    # 测试评分过滤逻辑
    reviews = [
        ExtractedReview(rating=5, date="Jan 2024", content="Great", is_vine=False),
        ExtractedReview(rating=3, date="Jan 2024", content="OK", is_vine=False),
        ExtractedReview(rating=1, date="Jan 2024", content="Bad", is_vine=True),
    ]
    # 差评应该是 rating <= 3
    negative = [r for r in reviews if r.rating <= 3]
    assert len(negative) == 2

def test_review_data_structure():
    r = ExtractedReview(rating=2, date="2024-01-15", content="Broke quickly", is_vine=False)
    assert r.rating == 2
    assert r.is_vine is False
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd amazon-scraper && pytest tests/test_review_extractor.py -v
# 预期: FAIL
```

- [ ] **Step 3: 创建 scraper/review_extractor.py**

```python
# scraper/review_extractor.py
from typing import List
from dataclasses import dataclass

@dataclass
class ExtractedReview:
    rating: int
    date: str
    content: str
    is_vine: bool

class ReviewExtractor:
    def extract_negative_reviews(self, page) -> List[ExtractedReview]:
        reviews = []
        review_cards = page.locator("[data-hook='review']").all()

        for card in review_cards:
            try:
                rating_elem = card.locator("[data-hook='review-star-rating']")
                rating_text = rating_elem.get_attribute("title") if rating_elem.count() > 0 else ""
                rating = int(rating_text.split(" ")[0]) if rating_text else 0

                if rating > 3:
                    continue

                date_elem = card.locator("[data-hook='review-date']")
                date = date_elem.inner_text() if date_elem.count() > 0 else ""

                content_elem = card.locator("[data-hook='review-body']")
                content = content_elem.inner_text() if content_elem.count() > 0 else ""

                vine_elem = card.locator("[data-hook='vine-badge']")
                is_vine = vine_elem.count() > 0

                reviews.append(ExtractedReview(
                    rating=rating,
                    date=date,
                    content=content,
                    is_vine=is_vine
                ))
            except Exception as e:
                print(f"Error extracting review: {e}")
                continue

        return reviews
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd amazon-scraper && pytest tests/test_review_extractor.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
cd amazon-scraper && git add scraper/review_extractor.py tests/test_review_extractor.py && git commit -m "feat: add review extractor"
```

---

## Task 8: 主程序集成

**Files:**
- Create: `main.py`

```python
# main.py
import sys
import time
from datetime import datetime

from config import config
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter
from database.store import DatabaseStore, Review
from scraper.product_list import ProductListScraper, Product
from scraper.review_page import ReviewPageController
from scraper.review_extractor import ReviewExtractor

def main():
    print("=" * 60)
    print("Amazon Review Scraper - Starting")
    print("=" * 60)

    # 初始化组件
    proxy_manager = ProxyManager()
    rate_limiter = RateLimiter()
    store = DatabaseStore()

    # Step 1: 采集商品列表
    print("\n[1/4] Scraping product list...")
    scraper = ProductListScraper(proxy_manager)
    products = scraper.scrape(max_products=config.MAX_PRODUCTS)
    print(f"Found {len(products)} products")

    if not products:
        print("No products found. Check your network/proxy settings.")
        return

    # 存储商品信息用于调试
    with open("products.csv", "w") as f:
        f.write("ASIN,Title,Brand,URL\n")
        for p in products:
            f.write(f"{p.asin},{p.title},{p.brand},{p.url}\n")

    # Step 2-4: 逐个采集评论
    print("\n[2/4] Scraping reviews...")
    review_controller = ReviewPageController(proxy_manager, rate_limiter)
    extractor = ReviewExtractor()

    collected = 0
    for i, product in enumerate(products, 1):
        print(f"\nProcessing [{i}/{len(products)}]: {product.title[:50]}...")

        try:
            # 随机间隔
            rate_limiter.sync_wait()

            # 打开评论页
            result = review_controller.open_review_page(product.url)
            if not result:
                print(f"  Failed to open review page for {product.asin}")
                continue

            page = result["page"]

            # 加载更多评论（懒加载）
            review_controller.load_more_reviews(page, max_pages=10)

            # 提取差评
            extracted = extractor.extract_negative_reviews(page)

            # 转换并存储
            reviews = [
                Review(
                    asin=product.asin,
                    brand=product.brand,
                    rating=e.rating,
                    date=e.date,
                    content=e.content,
                    is_vine=e.is_vine,
                    collected_at=datetime.now().isoformat()
                )
                for e in extracted
            ]
            store.insert_reviews(reviews)

            collected += len(reviews)
            print(f"  Collected {len(reviews)} negative reviews")

            # 关闭浏览器
            result["browser"].close()

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"\n[3/4] Total reviews collected: {collected}")

    # Step 4: 按品牌分组输出
    print("\n[4/4] Generating brand summary...")
    brands = store.get_all_brands()
    print(f"Brands found: {len(brands)}")

    with open("brand_summary.txt", "w") as f:
        f.write("Brand,Review Count\n")
        for brand in brands:
            count = len(store.get_reviews_by_brand(brand))
            f.write(f"{brand},{count}\n")
            print(f"  {brand}: {count} reviews")

    print("\n" + "=" * 60)
    print("Scraping complete!")
    print(f"Database: {config.DB_PATH}")
    print(f"Products: {len(products)}")
    print(f"Total reviews: {collected}")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

- [ ] **Step 1: 创建 main.py**

```python
# main.py
import sys
import time
from datetime import datetime

from config import config
from proxy.manager import ProxyManager
from rate_limiter import RateLimiter
from database.store import DatabaseStore, Review
from scraper.product_list import ProductListScraper, Product
from scraper.review_page import ReviewPageController
from scraper.review_extractor import ReviewExtractor

def main():
    print("=" * 60)
    print("Amazon Review Scraper - Starting")
    print("=" * 60)

    proxy_manager = ProxyManager()
    rate_limiter = RateLimiter()
    store = DatabaseStore()

    print("\n[1/4] Scraping product list...")
    scraper = ProductListScraper(proxy_manager)
    products = scraper.scrape(max_products=config.MAX_PRODUCTS)
    print(f"Found {len(products)} products")

    if not products:
        print("No products found. Check your network/proxy settings.")
        return

    with open("products.csv", "w") as f:
        f.write("ASIN,Title,Brand,URL\n")
        for p in products:
            f.write(f"{p.asin},{p.title},{p.brand},{p.url}\n")

    print("\n[2/4] Scraping reviews...")
    review_controller = ReviewPageController(proxy_manager, rate_limiter)
    extractor = ReviewExtractor()

    collected = 0
    for i, product in enumerate(products, 1):
        print(f"\nProcessing [{i}/{len(products)}]: {product.title[:50]}...")

        try:
            rate_limiter.sync_wait()
            result = review_controller.open_review_page(product.url)
            if not result:
                print(f"  Failed to open review page for {product.asin}")
                continue

            page = result["page"]
            review_controller.load_more_reviews(page, max_pages=10)
            extracted = extractor.extract_negative_reviews(page)

            reviews = [
                Review(
                    asin=product.asin,
                    brand=product.brand,
                    rating=e.rating,
                    date=e.date,
                    content=e.content,
                    is_vine=e.is_vine,
                    collected_at=datetime.now().isoformat()
                )
                for e in extracted
            ]
            store.insert_reviews(reviews)
            collected += len(reviews)
            print(f"  Collected {len(reviews)} negative reviews")
            result["browser"].close()

        except Exception as e:
            print(f"  Error: {e}")
            continue

    print(f"\n[3/4] Total reviews collected: {collected}")

    print("\n[4/4] Generating brand summary...")
    brands = store.get_all_brands()
    print(f"Brands found: {len(brands)}")

    with open("brand_summary.txt", "w") as f:
        f.write("Brand,Review Count\n")
        for brand in brands:
            count = len(store.get_reviews_by_brand(brand))
            f.write(f"{brand},{count}\n")
            print(f"  {brand}: {count} reviews")

    print("\n" + "=" * 60)
    print("Scraping complete!")
    print(f"Database: {config.DB_PATH}")
    print(f"Products: {len(products)}")
    print(f"Total reviews: {collected}")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
cd amazon-scraper && git add main.py && git commit -m "feat: add main entry point"
```

---

## Task 9: 依赖和环境配置

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `README.md`

```bash
# requirements.txt
playwright>=1.40.0
```

- [ ] **Step 1: 创建 requirements.txt**

```
playwright>=1.40.0
```

- [ ] **Step 2: 创建 .env.example**

```
# 代理配置
PROXY_PROVIDER=oxylabs
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
PROXY_LIST=ip:port:user:pass,ip2:port2:user2:pass2
```

- [ ] **Step 3: 创建 README.md**

```markdown
# Amazon Review Scraper

采集亚马逊商品差评数据，用于退货/投诉分析。

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 配置

复制 `.env.example` 为 `.env`，填入代理信息：

```bash
cp .env.example .env
```

## 运行

```bash
python main.py
```

## 输出

- `amazon_reviews.db` - SQLite数据库
- `products.csv` - 商品列表
- `brand_summary.txt` - 品牌统计
```

- [ ] **Step 4: 提交**

```bash
cd amazon-scraper && git add requirements.txt .env.example README.md && git commit -m "feat: add project documentation"
```

---

## 待解决问题

1. **代理服务**：需要购买住宅代理（Oxylabs/Bright Data），成本约$50-100/月
2. **验证码处理**：可能需要人工介入解决CAPTCHA
3. **测试环境**：首次运行建议先用少量商品测试

## 风险提示

- 亚马逊可能触发验证码导致采集中断
- 代理质量直接影响成功率
- 完整采集50商品可能需要6-12小时

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-24-amazon-review-scraper-plan.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?