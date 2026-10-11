from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from repositories.json_store import JsonStore


class ConfigRepository:
    """Kho cấu hình tổng của HMI.

    Cấu hình Vision/Camera/PLC được lưu phía PC. Các tham số chuyển động có
    ảnh hưởng trực tiếp tới máy vẫn phải được PLC kiểm tra giới hạn lần cuối.
    """

    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path)
        self.data: dict[str, Any] = {}
        self.load()

    def load(self) -> dict[str, Any]:
        raw = self.store.load()
        if not isinstance(raw, dict):
            raise ValueError("app_config.json phải là JSON object")
        self.data = raw
        return deepcopy(self.data)

    def save(self) -> None:
        self.store.save(self.data)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        current: Any = self.data
        for part in dotted_key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return deepcopy(current)

    def set(self, dotted_key: str, value: Any, *, save: bool = True) -> None:
        parts = dotted_key.split(".")
        current = self.data
        for part in parts[:-1]:
            child = current.get(part)
            if not isinstance(child, dict):
                child = {}
                current[part] = child
            current = child
        current[parts[-1]] = value
        if save:
            self.save()
