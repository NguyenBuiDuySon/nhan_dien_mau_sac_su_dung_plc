"""Nghiệp vụ quản lý màu, tách khỏi giao diện Vision.

ColorID chỉ thuộc màu; Destination và Routing không lưu trong ColorProfile.
Không tự động xóa Routing khi xóa một màu để tránh thao tác mất cấu hình.
"""

from __future__ import annotations

from copy import deepcopy

from app.state import ApplicationState
from domain.color_profile import ColorProfile, HSVRange
from repositories.color_repository import ColorRepository
from repositories.routing_repository import RoutingRepository


class ColorManagementService:
    def __init__(
        self,
        colors: ColorRepository,
        routes: RoutingRepository,
        state: ApplicationState,
    ) -> None:
        self.colors = colors
        self.routes = routes
        self.state = state

    def create(self, name: str, ui_color: str) -> ColorProfile:
        display_name = name.strip()
        key = self.colors.normalize_key(display_name)
        if not key:
            raise ValueError("Tên màu phải chứa ít nhất một ký tự hợp lệ.")
        if any(c.display_name.casefold() == display_name.casefold() for c in self.colors.all()):
            raise ValueError(f"Màu '{display_name}' đã tồn tại.")
        if any(c.key == key for c in self.colors.all()):
            raise ValueError(f"Color key '{key}' đã tồn tại.")

        next_id = max((c.id for c in self.colors.all()), default=0) + 1
        # Dải HSV mặc định chỉ là placeholder; màu mới phải được hiệu chỉnh rồi bật.
        profile = ColorProfile(
            id=next_id,
            key=key,
            display_name=display_name,
            ui_color=ui_color,
            enabled=False,
            hsv_ranges=[HSVRange(lower=(0, 0, 0), upper=(0, 0, 0))],
        )
        self.colors.add(profile)
        self.state.ensure_color(profile.id)
        return profile

    def update(self, color_id: int, name: str, ui_color: str, enabled: bool) -> ColorProfile:
        profile = deepcopy(self.colors.get(color_id))
        name = name.strip()
        if not name:
            raise ValueError("Tên màu không được để trống.")
        if any(c.id != color_id and c.display_name.casefold() == name.casefold() for c in self.colors.all()):
            raise ValueError(f"Tên màu '{name}' đã tồn tại.")
        if enabled and len(profile.hsv_ranges) == 1:
            hsv = profile.hsv_ranges[0]
            if hsv.lower == (0, 0, 0) and hsv.upper == (0, 0, 0):
                raise ValueError("Hãy cấu hình HSV trong Vision trước khi kích hoạt màu mới.")
        profile.display_name = name
        profile.ui_color = ui_color
        profile.enabled = enabled
        self.colors.update(profile)
        return profile

    def delete(self, color_id: int) -> None:
        # Màu đã gán vị trí không được xóa; người dùng gỡ Routing bên Manual trước.
        if self.routes.get_for_color(color_id) is not None:
            raise ValueError("Màu này đang có Routing. Hãy bỏ gán vị trí trong Manual trước khi xóa.")
        self.colors.remove(color_id)
        self.state.counters.pop(color_id, None)
        detection = self.state.current_detection
        if detection is not None and detection.color_id == color_id:
            self.state.current_detection = None
