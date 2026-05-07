"""System proxy detection for Windows."""

import subprocess
from typing import Optional


def get_system_proxy() -> Optional[dict]:
    """Read Windows system proxy settings from registry.

    Returns:
        {
            "server": "http://ip:port",
            "username": "xxx",  # optional
            "password": "xxx"    # optional
        }
        or None (proxy not enabled)
    """
    try:
        # Query registry for proxy settings
        # HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        result = subprocess.run(
            ["reg", "query", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyEnable"],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )

        # Check if proxy is enabled (value 0x1)
        if "0x1" not in result.stdout:
            return None

        # Get proxy server value
        result_server = subprocess.run(
            ["reg", "query", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings", "/v", "ProxyServer"],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=5
        )

        if not result_server.stdout:
            return None

        # Parse ProxyServer value (format: ip:port or ip:port:user:pass)
        lines = result_server.stdout.strip().split('\n')
        for line in lines:
            if "ProxyServer" in line:
                parts = line.split()
                if len(parts) >= 3:
                    proxy_value = parts[-1].strip()

                    # Check if it has authentication (user:pass@ip:port format)
                    if "@" in proxy_value:
                        auth_part, server_part = proxy_value.split("@")
                        if ":" in auth_part:
                            user, password = auth_part.split(":", 1)  # split(..., 1) in case password contains ":"
                        else:
                            # Auth format without password: user@server:port
                            user, password = auth_part, ""
                        return {
                            "server": f"http://{server_part}",
                            "username": user,
                            "password": password
                        }
                    else:
                        return {
                            "server": f"http://{proxy_value}",
                            "username": None,
                            "password": None
                        }

        return None

    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        # Registry access denied or reg command not found
        return None
    except Exception:
        # Any other error, silently return None
        return None
