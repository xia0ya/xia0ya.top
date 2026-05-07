"""Proxy manager module for handling proxy rotation and configuration."""

import os
from enum import Enum
from typing import List, Optional

from config import config

from proxy.system_proxy import get_system_proxy


class ProxyMode(Enum):
    """Proxy mode selection."""
    SYSTEM = "system"      # Read from Windows system proxy settings
    MANUAL = "manual"      # User-provided proxy string
    NONE = "none"          # No proxy


class ProxyManager:
    """Manages proxy list and rotation for Playwright browser automation."""

    def __init__(self, mode: ProxyMode = ProxyMode.SYSTEM, manual_proxy: Optional[str] = None) -> None:
        """Initialize ProxyManager with proxy mode.

        Args:
            mode: Proxy mode (SYSTEM, MANUAL, or NONE).
            manual_proxy: Manual proxy string in format "ip:port:user:pass" or "ip:port".
        """
        self.mode = mode
        self.manual_proxy = manual_proxy
        self._proxies: List[dict] = []
        self._current_index: int = 0

        # Add manual_proxy to _proxies for rotation support
        if mode == ProxyMode.MANUAL and manual_proxy:
            parsed = self._parse_manual_proxy(manual_proxy)
            if parsed:
                self._proxies.append(parsed)

    def _load_proxies(self) -> List[dict]:
        """Load proxies from PROXY_LIST environment variable.

        Proxy format: ip:port:username:password or ip:port (uses default credentials)

        Returns:
            List of proxy dictionaries with server, username, password keys.
        """
        proxy_list_env = os.getenv("PROXY_LIST", "").strip()

        if not proxy_list_env:
            return []

        proxies = []
        default_username = config.PROXY_USERNAME or "default_user"
        default_password = config.PROXY_PASSWORD or "default_pass"

        for proxy_str in proxy_list_env.split(","):
            proxy_str = proxy_str.strip()
            if not proxy_str:
                continue

            parts = proxy_str.split(":")

            if len(parts) == 4:
                # Full format: ip:port:username:password
                proxies.append({
                    "server": f"{parts[0]}:{parts[1]}",
                    "username": parts[2],
                    "password": parts[3],
                })
            elif len(parts) == 2:
                # Short format: ip:port (use default credentials)
                proxies.append({
                    "server": f"{parts[0]}:{parts[1]}",
                    "username": default_username,
                    "password": default_password,
                })

        return proxies

    def _parse_manual_proxy(self, proxy_str: str) -> Optional[dict]:
        """Parse manual proxy string.

        Args:
            proxy_str: Proxy string in format "user@ip:port", "ip:port:user:pass" or "ip:port".

        Returns:
            Proxy dictionary with server, username, password keys, or None if invalid.
        """
        if not proxy_str:
            return None

        proxy_str = proxy_str.strip()

        # Check for user@ip:port format
        if "@" in proxy_str:
            parts = proxy_str.split("@")
            if len(parts) == 2:
                user = parts[0]
                server_part = parts[1]
                server_parts = server_part.split(":")
                if len(server_parts) == 2:
                    return {
                        "server": f"{server_parts[0]}:{server_parts[1]}",
                        "username": user,
                        "password": "",
                    }

        parts = proxy_str.split(":")

        if len(parts) == 4:
            # Full format: ip:port:username:password
            return {
                "server": f"{parts[0]}:{parts[1]}",
                "username": parts[2],
                "password": parts[3],
            }
        elif len(parts) == 2:
            # Short format: ip:port (no authentication)
            return {
                "server": f"{parts[0]}:{parts[1]}",
                "username": None,
                "password": None,
            }

        return None

    def get_proxy(self) -> Optional[object]:
        """Get the current proxy in Playwright format based on mode.

        Returns:
            Proxy object with server, username, password attributes, or None if no proxies.
        """
        if self.mode == ProxyMode.NONE:
            return None

        if self.mode == ProxyMode.SYSTEM:
            system_proxy = get_system_proxy()
            if system_proxy is None:
                return None
            return _PlaywrightProxy(
                server=system_proxy["server"],
                username=system_proxy.get("username"),
                password=system_proxy.get("password"),
            )

        if self.mode == ProxyMode.MANUAL:
            # Return proxy from _proxies list (supports rotation)
            if not self._proxies:
                return None
            proxy_dict = self._proxies[self._current_index]
            return _PlaywrightProxy(
                server=f"http://{proxy_dict['server']}",
                username=proxy_dict.get("username"),
                password=proxy_dict.get("password"),
            )

        # SYSTEM/NONE mode: fallback to env-based proxy list
        if not self._proxies:
            self._proxies = self._load_proxies()

        if not self._proxies:
            return None

        proxy_dict = self._proxies[self._current_index]
        return _PlaywrightProxy(
            server=f"http://{proxy_dict['server']}",
            username=proxy_dict["username"],
            password=proxy_dict["password"],
        )

    def rotate(self) -> Optional[object]:
        """Rotate to the next proxy in the list.

        Returns:
            Next proxy object in Playwright format, or None if no proxies.
        """
        if self.mode == ProxyMode.MANUAL:
            # Rotate through _proxies list (manual_proxy is added in __init__)
            if not self._proxies:
                return None
            self._current_index = (self._current_index + 1) % len(self._proxies)
            return self.get_proxy()

        # SYSTEM/NONE mode: rotation not supported via rotate().
        # These modes obtain proxy from system settings each time get_proxy() is called.
        # If you need rotation, use MANUAL mode with proxy list in PROXY_LIST env var.
        return self.get_proxy()

    def set_manual_proxy(self, proxy_str: str) -> None:
        """Set manual proxy string.

        Args:
            proxy_str: Proxy string in format "ip:port:user:pass" or "ip:port".
        """
        self.mode = ProxyMode.MANUAL
        self.manual_proxy = proxy_str
        self._current_index = 0
        # Add to _proxies for rotation support
        self._proxies = []
        parsed = self._parse_manual_proxy(proxy_str)
        if parsed:
            self._proxies.append(parsed)


class _PlaywrightProxy:
    """Internal class representing a Playwright proxy configuration."""

    def __init__(self, server: str, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """Initialize Playwright proxy.

        Args:
            server: Proxy server URL (e.g., http://192.168.1.1:8080).
            username: Proxy authentication username (optional).
            password: Proxy authentication password (optional).
        """
        self.server = server
        self.username = username
        self.password = password

    def __repr__(self) -> str:
        """Return string representation of proxy."""
        return f"_PlaywrightProxy(server={self.server!r}, username={self.username!r}, password={self.password!r})"
