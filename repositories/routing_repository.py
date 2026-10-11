from __future__ import annotations

from pathlib import Path

from domain.routing import RoutingRule
from repositories.json_store import JsonStore


class RoutingRepository:
    """Lưu quan hệ Color -> Destination.

    Mỗi màu có tối đa một đích đang dùng. Nhiều màu được phép trỏ tới cùng
    một Destination, đúng với yêu cầu nhiều màu chung một vị trí.
    """

    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path)
        self._rules: dict[int, RoutingRule] = {}
        self.load()

    def load(self) -> None:
        raw = self.store.load()
        self._rules = {
            int(item["color_id"]): RoutingRule(
                color_id=int(item["color_id"]),
                destination_id=int(item["destination_id"]),
                enabled=bool(item.get("enabled", True)),
            )
            for item in raw
        }

    def save(self) -> None:
        self.store.save(
            [
                {
                    "color_id": rule.color_id,
                    "destination_id": rule.destination_id,
                    "enabled": rule.enabled,
                }
                for rule in sorted(self._rules.values(), key=lambda value: value.color_id)
            ]
        )

    def all(self) -> list[RoutingRule]:
        return list(sorted(self._rules.values(), key=lambda item: item.color_id))

    def get_for_color(self, color_id: int) -> RoutingRule | None:
        return self._rules.get(color_id)

    def set_route(self, color_id: int, destination_id: int, enabled: bool = True) -> None:
        self._rules[color_id] = RoutingRule(color_id, destination_id, enabled)
        self.save()

    def remove_route(self, color_id: int) -> None:
        self._rules.pop(color_id, None)
        self.save()
