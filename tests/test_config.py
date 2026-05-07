"""Tests for config module."""

import os
import unittest
from unittest.mock import patch

from config import Config, config


class TestConfig(unittest.TestCase):
    """Test suite for Config dataclass."""

    def test_base_url_default(self):
        """Test that BASE_URL is set to Amazon Best Sellers electric toothbrush."""
        cfg = Config()
        self.assertEqual(
            cfg.BASE_URL,
            "https://www.amazon.com/best-sellers-electric-toothbrushes/s?k=electric+toothbrush",
        )

    def test_db_path_default(self):
        """Test that DB_PATH defaults to database/products.db."""
        cfg = Config()
        self.assertEqual(cfg.DB_PATH, "database/products.db")

    def test_proxy_env_vars(self):
        """Test that proxy settings are read from environment variables."""
        with patch.dict(
            os.environ,
            {
                "PROXY_PROVIDER": "test_provider",
                "PROXY_USERNAME": "test_user",
                "PROXY_PASSWORD": "test_pass",
            },
        ):
            cfg = Config()
            self.assertEqual(cfg.PROXY_PROVIDER, "test_provider")
            self.assertEqual(cfg.PROXY_USERNAME, "test_user")
            self.assertEqual(cfg.PROXY_PASSWORD, "test_pass")

    def test_proxy_env_vars_empty_when_not_set(self):
        """Test that proxy settings default to empty strings."""
        cfg = Config()
        self.assertEqual(cfg.PROXY_PROVIDER, "")
        self.assertEqual(cfg.PROXY_USERNAME, "")
        self.assertEqual(cfg.PROXY_PASSWORD, "")

    def test_config_instance_exists(self):
        """Test that a config instance is exported."""
        self.assertIsNotNone(config)
        self.assertIsInstance(config, Config)

    def test_config_instance_has_expected_values(self):
        """Test that the exported config instance has expected values."""
        self.assertEqual(config.MAX_PRODUCTS, 50)
        self.assertEqual(config.MIN_DELAY, 8.0)
        self.assertEqual(config.MAX_DELAY, 15.0)
        self.assertIsNotNone(config.BASE_URL)
        self.assertIsNotNone(config.DB_PATH)


if __name__ == "__main__":
    unittest.main()
