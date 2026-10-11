from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStore:
    """Đọc/ghi JSON dùng file tạm để giảm rủi ro hỏng cấu hình giữa chừng."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Any:
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temp_path.replace(self.path)
