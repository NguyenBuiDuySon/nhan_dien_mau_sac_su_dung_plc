from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RoutingRule:
    """Ánh xạ Color -> Destination.

    Đây là lớp tách Vision khỏi cơ khí. PLC không cần biết HSV hay tên màu;
    PLC chỉ nhận đích đã được RoutingService giải quyết.
    """

    color_id: int
    destination_id: int
    enabled: bool = True
