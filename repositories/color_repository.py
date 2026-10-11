from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from domain.color_profile import ColorProfile, HSVRange
from repositories.json_store import JsonStore


class ColorRepository:
    """Kho màu của V04.

    Khác V03 ở chỗ ColorProfile không chứa tọa độ. Việc màu nào đi tới đâu
    thuộc RoutingRepository/RouteService.
    """

    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path)
        self._items: dict[int, ColorProfile] = {}
        self.load()

    def load(self) -> None:
        raw = self.store.load()
        items: dict[int, ColorProfile] = {}
        for item in raw:
            profile = ColorProfile(
                id=int(item["id"]),
                key=str(item["key"]),
                display_name=str(item["display_name"]),
                ui_color=str(item.get("ui_color", "#94a3b8")),
                enabled=bool(item.get("enabled", True)),
                min_confidence=(
                    float(item["min_confidence"])
                    if item.get("min_confidence") is not None
                    else None
                ),
                hsv_ranges=[
                    HSVRange(
                        lower=tuple(map(int, hsv["lower"])),
                        upper=tuple(map(int, hsv["upper"])),
                    )
                    for hsv in item.get("hsv_ranges", [])
                ],
            )
            profile.validate()
            if profile.id in items:
                raise ValueError(f"Trùng Color ID: {profile.id}")
            items[profile.id] = profile
        self._items = items

    def save(self) -> None:
        self.store.save(
            [
                {
                    "id": item.id,
                    "key": item.key,
                    "display_name": item.display_name,
                    "ui_color": item.ui_color,
                    "enabled": item.enabled,
                    "min_confidence": item.min_confidence,
                    "hsv_ranges": [
                        {"lower": list(r.lower), "upper": list(r.upper)}
                        for r in item.hsv_ranges
                    ],
                }
                for item in sorted(self._items.values(), key=lambda value: value.id)
            ]
        )

    def all(self) -> list[ColorProfile]:
        return list(sorted(self._items.values(), key=lambda item: item.id))

    def enabled(self) -> list[ColorProfile]:
        return [item for item in self.all() if item.enabled]

    def get(self, color_id: int) -> ColorProfile:
        try:
            return self._items[color_id]
        except KeyError as error:
            raise KeyError(f"Không tồn tại Color ID {color_id}") from error

    def get_by_key(self, key: str) -> ColorProfile:
        normalized = self.normalize_key(key)
        for item in self._items.values():
            if item.key == normalized:
                return item
        raise KeyError(f"Không tồn tại màu '{key}'")

    def add(self, profile: ColorProfile) -> None:
        profile.validate()
        if profile.id in self._items:
            raise ValueError(f"Color ID {profile.id} đã tồn tại")
        if any(item.key == profile.key for item in self._items.values()):
            raise ValueError(f"Color key '{profile.key}' đã tồn tại")
        self._items[profile.id] = profile
        self.save()

    def update(self, profile: ColorProfile) -> None:
        profile.validate()
        if profile.id not in self._items:
            raise KeyError(f"Không tồn tại Color ID {profile.id}")
        self._items[profile.id] = profile
        self.save()

    def set_enabled(self, color_id: int, enabled: bool) -> None:
        self.get(color_id).enabled = enabled
        self.save()

    @staticmethod
    def normalize_key(name: str) -> str:
        normalized = unicodedata.normalize("NFD", name.strip().lower())
        ascii_text = "".join(
            char for char in normalized if unicodedata.category(char) != "Mn"
        ).replace("đ", "d")
        return re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
