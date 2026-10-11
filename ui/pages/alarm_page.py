from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.context import ApplicationContext
from ui.pages.base_page import BasePage
from ui.widgets import SectionCard, StatusLed


class AlarmPage(BasePage):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH ALARM",
            "Hiển thị và quản lý cảnh báo, lỗi của PLC và các thiết bị ngoại vi",
            "⚠",
        )
        self.context = context

        content = QHBoxLayout()
        content.setSpacing(10)
        left = QVBoxLayout()

        current_body = QWidget()
        current_layout = QHBoxLayout(current_body)
        self.current_led = StatusLed("Không có lỗi", True)
        self.current_text = QLabel("Hệ thống đang hoạt động bình thường")
        self.current_text.setObjectName("metricValue")
        self.current_text.setStyleSheet("font-size:23px; color:#34d976;")
        current_layout.addWidget(self.current_led)
        current_layout.addWidget(self.current_text, 1)
        left.addWidget(SectionCard("ALARM HIỆN TẠI", current_body, title_icon="⚠"))

        self.history = QTableWidget(0, 5)
        self.history.setHorizontalHeaderLabels(["THỜI GIAN", "MÃ LỖI", "MÔ TẢ", "MỨC ĐỘ", "TRẠNG THÁI"])
        self.history.setAlternatingRowColors(True)
        left.addWidget(SectionCard("LỊCH SỬ ALARM", self.history, title_icon="↶"), 1)

        actions = QHBoxLayout()
        mute = QPushButton("Tắt còi báo")
        ack = QPushButton("✓  Xác nhận Alarm")
        reset = QPushButton("↻  Reset lỗi")
        ack.setObjectName("pauseButton")
        reset.setObjectName("resetButton")
        reset.clicked.connect(self.context.plc.reset)
        actions.addWidget(mute)
        actions.addStretch()
        actions.addWidget(ack)
        actions.addWidget(reset)
        left.addLayout(actions)
        content.addLayout(left, 5)

        device_body = QWidget()
        device_layout = QVBoxLayout(device_body)
        self.device_leds = {
            "plc": StatusLed("PLC S7-1200"),
            "camera": StatusLed("Camera"),
            "sensor": StatusLed("Cảm biến"),
            "conveyor": StatusLed("Băng tải"),
            "vacuum": StatusLed("Nguồn khí / Vacuum"),
            "servo": StatusLed("Servo / Axis"),
        }
        for led in self.device_leds.values():
            device_layout.addWidget(led)
        device_layout.addStretch()
        content.addWidget(SectionCard("TRẠNG THÁI THIẾT BỊ", device_body, title_icon="⚙"), 2)
        self.root.addLayout(content, 1)
        self.refresh()

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        if status.fault_code:
            self.current_led.set_text(f"FAULT {status.fault_code}")
            self.current_led.set_active(False, fault=True)
            self.current_text.setText(f"PLC báo lỗi mã {status.fault_code}")
            self.current_text.setStyleSheet("font-size:23px; color:#ef4444;")
        else:
            self.current_led.set_text("Không có lỗi")
            self.current_led.set_active(True)
            self.current_text.setText("Hệ thống đang hoạt động bình thường")
            self.current_text.setStyleSheet("font-size:23px; color:#34d976;")

        self.device_leds["plc"].set_active(status.connected, fault=not status.connected)
        self.device_leds["camera"].set_active(self.context.camera.running)
        self.device_leds["sensor"].set_active(status.product_sensor)
        self.device_leds["conveyor"].set_active(status.connected)
        self.device_leds["vacuum"].set_active(status.vacuum_ready)
        self.device_leds["servo"].set_active(status.servo_ready)

        records = list(self.context.state.recent_alarms)
        if status.fault_code and not records:
            records.append((datetime.now().strftime("%d/%m/%Y %H:%M:%S"), str(status.fault_code), "PLC Fault", "Cao"))
        self.history.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [*record, "Đang xảy ra" if row == 0 and status.fault_code else "Đã ghi nhận"]
            for column, value in enumerate(values):
                self.history.setItem(row, column, QTableWidgetItem(str(value)))
