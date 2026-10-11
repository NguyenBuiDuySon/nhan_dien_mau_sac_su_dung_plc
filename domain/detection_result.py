from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DetectionResult:
    """Kết quả chuẩn hóa từ pipeline Vision."""

    color_id: int | None
    color_key: str | None
    confidence: float
    stable: bool
