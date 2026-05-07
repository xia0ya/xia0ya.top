import customtkinter as ctk


class ProgressView(ctk.CTkFrame):
    """进度显示框：链接进度 + 评论计数 + 进度条"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.link_label = ctk.CTkLabel(self, text="链接: 0/0")
        self.link_label.pack(pady=(0, 5))

        self.review_label = ctk.CTkLabel(self, text="已采集: 0 条评论")
        self.review_label.pack(pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)

        self.percent_label = ctk.CTkLabel(self, text="0%")
        self.percent_label.pack()

    def update(self, completed_links: int, total_links: int, review_count: int) -> None:
        self.link_label.configure(text=f"链接: {completed_links}/{total_links}")
        self.review_label.configure(text=f"已采集: {review_count} 条评论")
        if total_links > 0:
            percent = completed_links / total_links
            self.progress_bar.set(percent)
            self.percent_label.configure(text=f"{int(percent * 100)}%")
        else:
            self.progress_bar.set(0)
            self.percent_label.configure(text="0%")
