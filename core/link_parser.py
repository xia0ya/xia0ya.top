import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse


class LinkType(Enum):
    PRODUCT = "product"      # 商品页 /dp/ASIN
    REVIEW = "review"        # 评论页 /product-reviews/ASIN
    UNKNOWN = "unknown"


@dataclass
class ParsedLink:
    original: str
    asin: str
    link_type: LinkType
    review_url: str


class LinkParser:
    ASIN_PATTERN = r'(B0[A-Z0-9]{8})'

    @classmethod
    def extract_asin(cls, text: str) -> Optional[str]:
        """从文本中提取 ASIN"""
        match = re.search(cls.ASIN_PATTERN, text, re.IGNORECASE)
        return match.group(1) if match else None

    @classmethod
    def detect_link_type(cls, url: str) -> LinkType:
        """检测链接类型"""
        parsed = urlparse(url.lower())
        if '/product-reviews/' in parsed.path:
            return LinkType.REVIEW
        if '/dp/' in parsed.path or '/gp/product/' in parsed.path:
            return LinkType.PRODUCT
        if cls.extract_asin(url):
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
        """解析单个链接"""
        asin = cls.extract_asin(url)
        if not asin:
            return None
        link_type = cls.detect_link_type(url)
        review_url = cls.to_review_url(url)
        return ParsedLink(
            original=url,
            asin=asin,
            link_type=link_type,
            review_url=review_url
        )

    @classmethod
    def parse_multi(cls, text: str) -> List[ParsedLink]:
        """解析多行文本中的所有链接"""
        seen = set()
        results = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = cls.parse(line)
            if parsed and parsed.asin not in seen:
                seen.add(parsed.asin)
                results.append(parsed)
        return results

    @classmethod
    def parse_file(cls, filepath: str) -> List[ParsedLink]:
        """从文件读取并解析链接"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls.parse_multi(content)
