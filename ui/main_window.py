from __future__ import annotations

from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from ui.pages.alarm_page import AlarmPage
from ui.pages.auto_page import AutoPage
from ui.pages.manual_page import ManualPage
from ui.pages.overview_page import OverviewPage
from ui.pages.vision_page import VisionPage
from ui.widgets import StatusLed


class MainWindow(QMainWindow):
    """Khung HMI chung: Header + Sidebar + QStackedWidget.

    MainWindow chỉ điều phối UI. Logic Camera, Routing và PLC nằm trong service
    riêng để các screen không sở hữu connection riêng và không lệch trạng thái.
    """

    NAV_ITEMS = (
        "Tổng quan",
        "Auto",
        "Manual",
        "Vision",
        "Alarm",
    )

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self.context = context
        # Các màn hình đều kế thừa QWidget.
        # Khai báo kiểu rõ ràng để Pylance biết QStackedWidget có thể nhận chúng.
        self.pages: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self.setWindowTitle("Hệ thống phân loại màu - PLC | V04")
        self.resize(1680, 960)
        self.setMinimumSize(1280, 760)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.pages.update(
        {
            "Tổng quan": OverviewPage(context),
            "Auto": AutoPage(context),
            "Manual": ManualPage(context),
            "Vision": VisionPage(context),
            "Alarm": AlarmPage(context),
        }
    )
        for page in self.pages.values():
            self.stack.addWidget(page)
        body_layout.addWidget(self.stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        vision_page = self.pages.get("Vision")
        if isinstance(vision_page, VisionPage):
            vision_page.colors_changed.connect(self._on_colors_changed)

        self._activate_page("Tổng quan")
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(400)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

        if bool(self.context.config.get("camera.auto_start", False)):
            self.context.camera.start(
                self.context.config.get("camera.source", 0),
                int(self.context.config.get("camera.width", 1280)),
                int(self.context.config.get("camera.height", 720)),
                int(self.context.config.get("camera.fps", 30)),
            )
        self.refresh()

    def _on_colors_changed(self) -> None:
        """Cập nhật bộ đếm và bảng Routing sau khi sửa màu ở Vision."""
        for page in self.pages.values():
            rebuild = getattr(page, "_rebuild_counter_rows", None)
            if callable(rebuild):
                rebuild()
        manual_page = self.pages.get("Manual")
        if isinstance(manual_page, ManualPage):
            manual_page._refresh_route_table()

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(92)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 10, 28, 10)
        layout.setSpacing(20)

        title = QLabel("HỆ THỐNG PHÂN LOẠI MÀU - PLC")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        layout.addStretch(1)

        self.header_plc = StatusLed(
            "PLC S7-1200\nĐang kết nối"
        )
        self.header_plc.setMinimumWidth(190)

        self.header_camera = StatusLed(
            "Camera\nOffline"
        )
        self.header_camera.setMinimumWidth(160)

        self.header_mode = QLabel("Chế độ\n--")
        self.header_mode.setObjectName("headerMode")
        self.header_mode.setMinimumWidth(110)

        self.header_clock = QLabel("--:--:--\n--/--/----")
        self.header_clock.setObjectName("headerClock")
        self.header_clock.setMinimumWidth(115)

        layout.addWidget(self.header_plc)
        layout.addWidget(self._divider())

        layout.addWidget(self.header_camera)
        layout.addWidget(self._divider())

        layout.addWidget(self.header_mode)
        layout.addWidget(self._divider())

        layout.addWidget(self.header_clock)

        return header

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setObjectName("headerDivider")
        return line

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(268)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 18, 0, 18)
        layout.setSpacing(6)

        brand = QLabel("V04 PLC\nCOLOR SORTING")
        brand.setObjectName("sidebarBrand")
        layout.addWidget(brand)

        for name in self.NAV_ITEMS:
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setProperty("active", False)

            button.clicked.connect(
                lambda checked=False, page=name: self._activate_page(page)
            )

            self.nav_buttons[name] = button
            layout.addWidget(button)
        layout.addStretch()

        version = QLabel("PLC HMI V04\nPySide6 + python-snap7")
        version.setObjectName("sidebarVersion")
        layout.addWidget(version)
        return sidebar

    def _activate_page(self, name: str) -> None:
        """Chuyển màn hình hiện tại theo tên sidebar."""
        page = self.pages.get(name)
        if page is not None:
            self.stack.setCurrentWidget(page)

        for button_name, button in self.nav_buttons.items():
            button.setProperty("active", button_name == name)
            button.style().unpolish(button)
            button.style().polish(button)

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        driver = str(self.context.config.get("plc.driver", "mock")).strip().lower()
        plc_name = "PLC MOCK" if driver == "mock" else "PLC S7-1200"
        plc_state = "Mô phỏng" if driver == "mock" else ("Đã kết nối" if status.connected else "Mất kết nối")
        self.header_plc.set_text(f"{plc_name}\n{plc_state}")
        self.header_plc.set_active(status.connected, fault=not status.connected)
        self.header_camera.set_text("Camera\nOnline" if self.context.camera.running else "Camera\nOffline")
        self.header_camera.set_active(self.context.camera.running)
        mode_color = "#22d3ee" if status.mode.value == "AUTO" else "#35e4d3"
        self.header_mode.setText(f"Chế độ\n{status.mode.value}")
        self.header_mode.setStyleSheet(f"color:{mode_color};")
        
        now = QDateTime.currentDateTime()
        self.header_clock.setText(
            now.toString("HH:mm:ss\ndd/MM/yyyy")
        )

        page = self.stack.currentWidget()
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            refresh()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.refresh_timer.stop()
        self.context.close()
        super().closeEvent(event)
