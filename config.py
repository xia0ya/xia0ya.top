"""Configuration module for Amazon scraper."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    """Configuration settings for the Amazon scraper."""

    MAX_PRODUCTS: int = 50
    MIN_DELAY: float = 8.0
    MAX_DELAY: float = 15.0

    PROXY_PROVIDER: str = ""
    PROXY_USERNAME: str = ""
    PROXY_PASSWORD: str = ""

    BASE_URL: str = "https://www.amazon.com/Best-Sellers-Health-Household-Rotating-Power-Toothbrushes/zgbs/hpc/18065349011/ref=zg_bs_nav_hpc_5_18065347011"
    DB_PATH: str = "database/products.db"

    def __post_init__(self):
        """Read environment variables for proxy settings."""
        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(self, "PROXY_PROVIDER", os.getenv("PROXY_PROVIDER", ""))
        object.__setattr__(self, "PROXY_USERNAME", os.getenv("PROXY_USERNAME", ""))
        object.__setattr__(self, "PROXY_PASSWORD", os.getenv("PROXY_PASSWORD", ""))


config = Config()
