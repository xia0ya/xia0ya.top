import customtkinter as ctk
from proxy.manager import ProxyMode


class ConfigPanel(ctk.CTkFrame):
    """配置面板：代理模式 + 请求间隔 + Cookie文件"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # 代理模式
        self.proxy_mode_var = ctk.StringVar(value="system")
        ctk.CTkRadioButton(
            self, text="系统代理 (VPN)",
            variable=self.proxy_mode_var, value="system"
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ctk.CTkRadioButton(
            self, text="手动输入",
            variable=self.proxy_mode_var, value="manual"
        ).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # 手动代理输入
        self.manual_proxy_entry = ctk.CTkEntry(self, width=250, placeholder_text="ip:port:user:pass")
        self.manual_proxy_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # 请求间隔
        ctk.CTkLabel(self, text="请求间隔 (秒)").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.min_delay_entry = ctk.CTkEntry(self, width=60, placeholder_text="8")
        self.min_delay_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(self, text=" - ").grid(row=2, column=2, sticky="w", padx=0, pady=5)
        self.max_delay_entry = ctk.CTkEntry(self, width=60, placeholder_text="15")
        self.max_delay_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)

        # Cookie文件
        ctk.CTkLabel(self, text="Cookie文件").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.cookie_entry = ctk.CTkEntry(self, width=200, placeholder_text="cookies.json")
        self.cookie_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.cookie_entry.insert(0, "cookies.json")
        ctk.CTkButton(
            self, text="浏览", width=60, command=self._browse_cookie
        ).grid(row=3, column=2, sticky="w", padx=5, pady=5)

    def _browse_cookie(self) -> None:
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if filename:
            self.cookie_entry.delete(0, "end")
            self.cookie_entry.insert(0, filename)

    def get_proxy_mode(self) -> ProxyMode:
        mode = self.proxy_mode_var.get()
        if mode == "manual":
            return ProxyMode.MANUAL
        return ProxyMode.SYSTEM

    def get_manual_proxy(self) -> str | None:
        proxy = self.manual_proxy_entry.get().strip()
        return proxy if proxy else None

    def get_min_delay(self) -> float:
        try:
            return float(self.min_delay_entry.get().strip())
        except ValueError:
            return 8.0

    def get_max_delay(self) -> float:
        try:
            return float(self.max_delay_entry.get().strip())
        except ValueError:
            return 15.0

    def get_cookie_path(self) -> str:
        return self.cookie_entry.get().strip() or "cookies.json"
