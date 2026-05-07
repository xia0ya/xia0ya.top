import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set


@dataclass
class ProgressState:
    total: int = 0
    completed: Set[str] = field(default_factory=set)
    last_updated: str = ""

    def mark_completed(self, asin: str) -> None:
        if asin not in self.completed:
            self.completed.add(asin)
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def is_completed(self, asin: str) -> bool:
        return asin in self.completed

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "completed": list(self.completed),
            "last_updated": self.last_updated
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressState":
        return cls(
            total=data.get("total", 0),
            completed=set(data.get("completed", [])),
            last_updated=data.get("last_updated", "")
        )


class ProgressTracker:
    def __init__(self, filepath: str = "progress.json"):
        self.filepath = filepath
        self.state = ProgressState()
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.state = ProgressState.from_dict(data)
            except (json.JSONDecodeError, IOError):
                self.state = ProgressState()

    def _save(self) -> None:
        with self._lock:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)

    def init(self, total: int) -> None:
        with self._lock:
            self.state.total = total
            self.state.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._save()

    def mark_completed(self, asin: str) -> None:
        with self._lock:
            self.state.mark_completed(asin)
            self._save()

    def is_completed(self, asin: str) -> bool:
        return self.state.is_completed(asin)

    def get_remaining(self, all_asins: List[str]) -> List[str]:
        return [asin for asin in all_asins if not self.is_completed(asin)]

    def reset(self) -> None:
        with self._lock:
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
            self.state = ProgressState()
