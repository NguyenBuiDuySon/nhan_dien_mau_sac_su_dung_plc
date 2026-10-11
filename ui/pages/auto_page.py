from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget, QPushButton

from app.context import ApplicationContext
from domain.machine import MachineMode, MachineState
from ui.pages.base_page import BasePage
from ui.widgets import CameraView, CounterRow, SectionCard, StatusLed


class AutoPage(BasePage):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH AUTO",
            "Hệ thống chạy tự động và phân loại sản phẩm theo cấu hình Routing",
            "◴",
        )
        self.context = context

        content = QHBoxLayout()
        content.setSpacing(10)
        self.camera_view = CameraView("CAMERA OFFLINE")
        self.context.camera.frame_ready.connect(self.camera_view.set_frame)
        content.addWidget(SectionCard("HÌNH ẢNH CAMERA TRỰC TIẾP", self.camera_view, title_icon="▣"), 5)

        right = QVBoxLayout()
        right.setSpacing(10)

        counter_body = QWidget()
        counter_layout = QVBoxLayout(counter_body)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        self.counter_rows: dict[int, CounterRow] = {}
        for color in self.context.colors.enabled():
            row = CounterRow(color.display_name, color.ui_color)
            self.counter_rows[color.id] = row
            counter_layout.addWidget(row)
        self.unknown_counter = CounterRow("Lỗi / Không xác định", "#94a3b8")
        counter_layout.addWidget(self.unknown_counter)
        counter_layout.addStretch()
        right.addWidget(SectionCard("BỘ ĐẾM SẢN PHẨM", counter_body, title_icon="▥"), 3)

        machine_body = QWidget()
        machine_layout = QVBoxLayout(machine_body)
        machine_layout.setContentsMargins(0, 0, 0, 0)
        self.machine_leds = {
            "conveyor": StatusLed("Băng tải"),
            "sensor": StatusLed("Cảm biến sản phẩm"),
            "homed": StatusLed("Trục đã Home"),
            "plc": StatusLed("PLC kết nối"),
            "safety": StatusLed("Liên động an toàn"),
        }
        for led in self.machine_leds.values():
            machine_layout.addWidget(led)
        machine_layout.addStretch()
        right.addWidget(SectionCard("TRẠNG THÁI MÁY", machine_body, title_icon="⚙"), 2)
        content.addLayout(right, 2)
        self.root.addLayout(content, 1)

        controls = QGridLayout()
        controls.setHorizontalSpacing(12)
        self.start_btn = QPushButton("▶  Start\nBắt đầu chạy")
        self.start_btn.setObjectName("startButton")
        self.pause_btn = QPushButton("Ⅱ  Pause\nTạm dừng")
        self.pause_btn.setObjectName("pauseButton")
        self.stop_btn = QPushButton("■  Stop\nDừng hệ thống")
        self.stop_btn.setObjectName("stopButton")
        self.reset_btn = QPushButton("↻  Reset\nReset máy")
        self.reset_btn.setObjectName("resetButton")
        for column, button in enumerate((self.start_btn, self.pause_btn, self.stop_btn, self.reset_btn)):
            controls.addWidget(button, 0, column)
        self.root.addLayout(controls)

        self.start_btn.clicked.connect(self.context.plc.start_auto)
        self.pause_btn.clicked.connect(self.context.plc.pause_auto)
        self.stop_btn.clicked.connect(self.context.plc.stop)
        self.reset_btn.clicked.connect(self.context.plc.reset)
        self.refresh()

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        self.machine_leds["conveyor"].set_active(status.conveyor_on)
        self.machine_leds["sensor"].set_active(status.product_sensor)
        self.machine_leds["homed"].set_active(status.axis_homed)
        self.machine_leds["plc"].set_active(status.connected, fault=not status.connected)
        self.machine_leds["safety"].set_active(status.safety_ok, fault=not status.safety_ok)

        can_start = (
            status.connected
            and status.mode == MachineMode.AUTO
            and status.state in {MachineState.READY, MachineState.PAUSED}
            and status.fault_code == 0
            and status.axis_homed
            and status.safety_ok
        )
        self.start_btn.setEnabled(can_start)
        self.pause_btn.setEnabled(status.state == MachineState.RUNNING)
        self.stop_btn.setEnabled(status.connected)
        self.reset_btn.setEnabled(status.connected)

        for color_id, row in self.counter_rows.items():
            row.set_count(self.context.state.counters.get(color_id, 0))
        self.unknown_counter.set_count(self.context.state.unknown_count)
