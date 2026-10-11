from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.state import ApplicationState
from repositories.color_repository import ColorRepository
from repositories.config_repository import ConfigRepository
from repositories.destination_repository import DestinationRepository
from repositories.routing_repository import RoutingRepository
from services.camera_service import CameraService
from services.mock_plc_service import MockPLCService
from services.plc_service import PLCService
from services.routing_service import RoutingService
from services.siemens_s7_plc_service import S7ConnectionConfig, SiemensS7PLCService


@dataclass(slots=True)
class ApplicationContext:
    """Dependency container dùng chung toàn ứng dụng.

    Các Page không được tự tạo PLC/camera service riêng. Mọi màn hình nhìn cùng
    một nguồn trạng thái để tránh lệch dữ liệu giữa Auto, Manual và Overview.
    """

    config: ConfigRepository
    colors: ColorRepository
    destinations: DestinationRepository
    routes: RoutingRepository
    routing_service: RoutingService
    plc: PLCService
    camera: CameraService
    state: ApplicationState

    @classmethod
    def create_default(cls) -> "ApplicationContext":
        root = Path(__file__).resolve().parent.parent
        config = ConfigRepository(root / "config" / "app_config.json")
        colors = ColorRepository(root / "config" / "colors.json")
        destinations = DestinationRepository(root / "config" / "destinations.json")
        routes = RoutingRepository(root / "config" / "routing.json")
        routing_service = RoutingService(colors, destinations, routes)

        driver = str(config.get("plc.driver", "mock")).strip().lower()
        if driver in {"s7", "siemens", "snap7"}:
            plc: PLCService = SiemensS7PLCService(
                S7ConnectionConfig(
                    host=str(config.get("plc.host", "192.168.0.10")),
                    rack=int(config.get("plc.rack", 0)),
                    slot=int(config.get("plc.slot", 1)),
                    tcp_port=int(config.get("plc.tcp_port", 102)),
                    command_db=int(config.get("plc.command_db", 100)),
                    status_db=int(config.get("plc.status_db", 101)),
                    poll_interval_s=float(config.get("plc.poll_interval_s", 0.2)),
                )
            )
        else:
            plc = MockPLCService()

        state = ApplicationState()
        for color in colors.all():
            state.ensure_color(color.id)

        return cls(
            config=config,
            colors=colors,
            destinations=destinations,
            routes=routes,
            routing_service=routing_service,
            plc=plc,
            camera=CameraService(),
            state=state,
        )

    def close(self) -> None:
        self.camera.close()
        self.plc.close()
