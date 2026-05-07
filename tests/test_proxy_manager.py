"""Tests for proxy manager module."""

import os
import unittest
from unittest.mock import patch

from proxy.manager import ProxyManager


class TestProxyManager(unittest.TestCase):
    """Test suite for ProxyManager class."""

    def test_load_proxies_parses_4_part_format(self):
        """Test that _load_proxies correctly parses ip:port:username:password format."""
        with patch.dict(os.environ, {"PROXY_LIST": "192.168.1.1:8080:user1:pass1"}):
            manager = ProxyManager()
            proxies = manager._load_proxies()
            self.assertEqual(len(proxies), 1)
            self.assertEqual(proxies[0], {
                "server": "192.168.1.1:8080",
                "username": "user1",
                "password": "pass1",
            })

    def test_load_proxies_parses_2_part_format(self):
        """Test that _load_proxies correctly parses ip:port format with default credentials."""
        with patch.dict(os.environ, {"PROXY_LIST": "192.168.1.1:8080"}):
            manager = ProxyManager()
            proxies = manager._load_proxies()
            self.assertEqual(len(proxies), 1)
            self.assertEqual(proxies[0], {
                "server": "192.168.1.1:8080",
                "username": "default_user",
                "password": "default_pass",
            })

    def test_load_proxies_parses_multiple_proxies(self):
        """Test that _load_proxies correctly parses multiple proxies separated by comma."""
        with patch.dict(
            os.environ,
            {
                "PROXY_LIST": "192.168.1.1:8080:user1:pass1,192.168.1.2:8081:user2:pass2,192.168.1.3:8082"
            },
        ):
            manager = ProxyManager()
            proxies = manager._load_proxies()
            self.assertEqual(len(proxies), 3)
            self.assertEqual(proxies[0]["server"], "192.168.1.1:8080")
            self.assertEqual(proxies[0]["username"], "user1")
            self.assertEqual(proxies[0]["password"], "pass1")
            self.assertEqual(proxies[1]["server"], "192.168.1.2:8081")
            self.assertEqual(proxies[1]["username"], "user2")
            self.assertEqual(proxies[1]["password"], "pass2")
            self.assertEqual(proxies[2]["server"], "192.168.1.3:8082")
            self.assertEqual(proxies[2]["username"], "default_user")
            self.assertEqual(proxies[2]["password"], "default_pass")

    def test_load_proxies_returns_empty_list_when_not_set(self):
        """Test that _load_proxies returns empty list when PROXY_LIST is not set."""
        with patch.dict(os.environ, {}, clear=True):
            manager = ProxyManager()
            proxies = manager._load_proxies()
            self.assertEqual(proxies, [])

    def test_load_proxies_returns_empty_list_when_empty_string(self):
        """Test that _load_proxies returns empty list when PROXY_LIST is empty string."""
        with patch.dict(os.environ, {"PROXY_LIST": ""}):
            manager = ProxyManager()
            proxies = manager._load_proxies()
            self.assertEqual(proxies, [])

    def test_get_proxy_returns_none_when_no_proxies(self):
        """Test that get_proxy returns None when proxy list is empty."""
        with patch.dict(os.environ, {}, clear=True):
            manager = ProxyManager()
            proxy = manager.get_proxy()
            self.assertIsNone(proxy)

    def test_get_proxy_returns_playwright_format(self):
        """Test that get_proxy returns Playwright format proxy config."""
        with patch.dict(os.environ, {"PROXY_LIST": "192.168.1.1:8080:user1:pass1"}):
            manager = ProxyManager()
            proxy = manager.get_proxy()
            self.assertIsNotNone(proxy)
            self.assertEqual(proxy.server, "http://192.168.1.1:8080")
            self.assertEqual(proxy.username, "user1")
            self.assertEqual(proxy.password, "pass1")

    def test_get_proxy_returns_2_part_format_with_defaults(self):
        """Test that get_proxy returns 2-part format proxy with default credentials."""
        with patch.dict(os.environ, {"PROXY_LIST": "192.168.1.1:8080"}):
            manager = ProxyManager()
            proxy = manager.get_proxy()
            self.assertIsNotNone(proxy)
            self.assertEqual(proxy.server, "http://192.168.1.1:8080")
            self.assertEqual(proxy.username, "default_user")
            self.assertEqual(proxy.password, "default_pass")

    def test_rotate_advances_to_next_proxy(self):
        """Test that rotate() advances to the next proxy in the list."""
        with patch.dict(
            os.environ,
            {"PROXY_LIST": "192.168.1.1:8080:user1:pass1,192.168.1.2:8081:user2:pass2"},
        ):
            manager = ProxyManager()
            first_proxy = manager.get_proxy()
            self.assertEqual(first_proxy.server, "http://192.168.1.1:8080")

            rotated_proxy = manager.rotate()
            self.assertEqual(rotated_proxy.server, "http://192.168.1.2:8081")

    def test_rotate_wraps_around_to_first_proxy(self):
        """Test that rotate() wraps around to the first proxy after the last."""
        with patch.dict(
            os.environ,
            {"PROXY_LIST": "192.168.1.1:8080:user1:pass1,192.168.1.2:8081:user2:pass2"},
        ):
            manager = ProxyManager()
            manager.get_proxy()  # Get first proxy
            manager.rotate()  # Move to second
            wrapped_proxy = manager.rotate()  # Wrap to first
            self.assertEqual(wrapped_proxy.server, "http://192.168.1.1:8080")

    def test_rotate_returns_none_when_no_proxies(self):
        """Test that rotate() returns None when proxy list is empty."""
        with patch.dict(os.environ, {}, clear=True):
            manager = ProxyManager()
            proxy = manager.rotate()
            self.assertIsNone(proxy)

    def test_get_proxy_maintains_rotation_state(self):
        """Test that get_proxy returns the same proxy when called consecutively without rotate."""
        with patch.dict(os.environ, {"PROXY_LIST": "192.168.1.1:8080:user1:pass1,192.168.1.2:8081:user2:pass2"}):
            manager = ProxyManager()
            first = manager.get_proxy()
            second = manager.get_proxy()
            self.assertEqual(first.server, second.server)


if __name__ == "__main__":
    unittest.main()
