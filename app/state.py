from __future__ import annotations

from dataclasses import dataclass, field

from domain.detection_result import DetectionResult


@dataclass(slots=True)
class ApplicationState:
    """State phía PC; không thay thế trạng thái authoritative từ PLC."""

    current_detection: DetectionResult | None = None
    counters: dict[int, int] = field(default_factory=dict)
    unknown_count: int = 0
    recent_alarms: list[tuple[str, str, str, str]] = field(default_factory=list)

    def ensure_color(self, color_id: int) -> None:
        self.counters.setdefault(color_id, 0)

    def reset_counters(self) -> None:
        for color_id in list(self.counters):
            self.counters[color_id] = 0
        self.unknown_count = 0
