from __future__ import annotations

from pathlib import Path

from domain.destination import Destination
from repositories.json_store import JsonStore


class DestinationRepository:
    """Quản lý các vị trí thả vật, độc lập với số lượng màu."""

    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path)
        self._items: dict[int, Destination] = {}
        self.load()

    def load(self) -> None:
        raw = self.store.load()
        items: dict[int, Destination] = {}
        for item in raw:
            destination = Destination(
                id=int(item["id"]),
                key=str(item["key"]),
                display_name=str(item["display_name"]),
                x=float(item["x"]),
                y=float(item["y"]),
                z=float(item["z"]),
                enabled=bool(item.get("enabled", True)),
            )
            destination.validate()
            if destination.id in items:
                raise ValueError(f"Trùng Destination ID: {destination.id}")
            items[destination.id] = destination
        self._items = items

    def save(self) -> None:
        self.store.save(
            [
                {
                    "id": item.id,
                    "key": item.key,
                    "display_name": item.display_name,
                    "x": item.x,
                    "y": item.y,
                    "z": item.z,
                    "enabled": item.enabled,
                }
                for item in sorted(self._items.values(), key=lambda value: value.id)
            ]
        )

    def all(self) -> list[Destination]:
        return list(sorted(self._items.values(), key=lambda item: item.id))

    def enabled(self) -> list[Destination]:
        return [item for item in self.all() if item.enabled]

    def get(self, destination_id: int) -> Destination:
        try:
            return self._items[destination_id]
        except KeyError as error:
            raise KeyError(f"Không tồn tại Destination ID {destination_id}") from error

    def add(self, destination: Destination) -> None:
        destination.validate()
        if destination.id in self._items:
            raise ValueError(f"Destination ID {destination.id} đã tồn tại")
        if any(item.key == destination.key for item in self._items.values()):
            raise ValueError(f"Destination key '{destination.key}' đã tồn tại")
        self._items[destination.id] = destination
        self.save()

    def update(self, destination: Destination) -> None:
        destination.validate()
        if destination.id not in self._items:
            raise KeyError(f"Không tồn tại Destination ID {destination.id}")
        self._items[destination.id] = destination
        self.save()

    def set_enabled(self, destination_id: int, enabled: bool) -> None:
        self.get(destination_id).enabled = enabled
        self.save()
