import customtkinter as ctk
from core.link_parser import LinkParser, ParsedLink


class LinkInput(ctk.CTkFrame):
    """链接输入框 + 文件导入 + 解析按钮"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.textbox = ctk.CTkTextbox(self, height=120)
        self.textbox.pack(fill="x", padx=5, pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=(0, 5))

        ctk.CTkButton(btn_frame, text="导入文件", command=self._import_file, width=100).pack(side="left")
        ctk.CTkButton(btn_frame, text="清空", command=self._clear, width=60).pack(side="left", padx=(5, 0))
        ctk.CTkButton(btn_frame, text="解析链接", command=self._parse, width=80).pack(side="left", padx=(5, 0))

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(anchor="w", padx=5, pady=(0, 5))

        self._parsed_links: list[ParsedLink] = []

    def _import_file(self) -> None:
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.textbox.delete("1.0", "end")
                self.textbox.insert("1.0", content)
                self.status_label.configure(text=f"已导入: {filename}", text_color="gray")
            except Exception as e:
                self.status_label.configure(text=f"导入失败: {e}", text_color="red")

    def _clear(self) -> None:
        self.textbox.delete("1.0", "end")
        self._parsed_links = []
        self.status_label.configure(text="")

    def _parse(self) -> None:
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            self.status_label.configure(text="请输入链接", text_color="orange")
            return
        self._parsed_links = LinkParser.parse_multi(text)
        count = len(self._parsed_links)
        if count > 0:
            self.status_label.configure(text=f"解析成功: {count} 个链接", text_color="green")
        else:
            self.status_label.configure(text="未解析到有效链接", text_color="orange")

    def get_links(self) -> list[ParsedLink]:
        return self._parsed_links
