from __future__ import annotations

from domain.destination import Destination
from repositories.color_repository import ColorRepository
from repositories.destination_repository import DestinationRepository
from repositories.routing_repository import RoutingRepository


class RoutingService:
    """Giải quyết màu nhận diện thành vị trí cơ khí.

    Đây là ranh giới chính giữa Vision và PLC:
    Vision -> color_id -> RoutingService -> Destination -> PLC.
    """

    def __init__(
        self,
        colors: ColorRepository,
        destinations: DestinationRepository,
        routes: RoutingRepository,
    ) -> None:
        self.colors = colors
        self.destinations = destinations
        self.routes = routes

    def resolve(self, color_id: int) -> Destination:
        color = self.colors.get(color_id)
        if not color.enabled:
            raise ValueError(f"Màu '{color.display_name}' đang bị vô hiệu hóa")

        rule = self.routes.get_for_color(color_id)
        if rule is None or not rule.enabled:
            raise LookupError(f"Màu '{color.display_name}' chưa có tuyến phân loại")

        destination = self.destinations.get(rule.destination_id)
        if not destination.enabled:
            raise ValueError(f"Vị trí '{destination.display_name}' đang bị vô hiệu hóa")
        return destination

    def colors_for_destination(self, destination_id: int) -> list[int]:
        """Trả danh sách Color ID đang dùng một Destination."""
        return [
            rule.color_id
            for rule in self.routes.all()
            if rule.enabled and rule.destination_id == destination_id
        ]

    def validate_configuration(self) -> list[str]:
        errors: list[str] = []
        for rule in self.routes.all():
            try:
                self.colors.get(rule.color_id)
            except KeyError:
                errors.append(f"Route tham chiếu Color ID {rule.color_id} không tồn tại")
            try:
                self.destinations.get(rule.destination_id)
            except KeyError:
                errors.append(
                    f"Route Color {rule.color_id} tham chiếu Destination "
                    f"{rule.destination_id} không tồn tại"
                )
        return errors
