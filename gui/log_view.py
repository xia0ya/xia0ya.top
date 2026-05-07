import customtkinter as ctk
from datetime import datetime
from queue import Queue, Empty


class LogView(ctk.CTkTextbox):
    """Scrolling log textbox with thread-safe updates."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(state="disabled")
        self.log_queue = Queue()
        self._poll_log()

    def append_log(self, message: str) -> None:
        """线程安全添加日志"""
        self.log_queue.put(message)

    def _poll_log(self) -> None:
        """定期检查日志队列"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._add_text(msg)
        except Empty:
            pass
        self.after(100, self._poll_log)

    def _add_text(self, message: str) -> None:
        self.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.insert("end", f"[{timestamp}] {message}\n")
        self.see("end")
        self.configure(state="disabled")
