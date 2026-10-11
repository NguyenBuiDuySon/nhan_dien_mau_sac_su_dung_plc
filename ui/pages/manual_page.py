from __future__ import annotations

from PySide6.QtWidgets import QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QVBoxLayout, QWidget

from app.context import ApplicationContext
from domain.machine import MachineMode
from ui.pages.base_page import BasePage
from ui.widgets import SectionCard, StatusLed


class ManualPage(BasePage):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH MANUAL",
            "Điều khiển tay các trục và thiết bị; PLC vẫn kiểm tra liên động trước khi chạy",
            "☝",
        )
        self.context = context
        self.axis_labels: dict[str, QLabel] = {}
        self.step_mm = 1.0

        axis_grid = QGridLayout()
        axis_grid.setSpacing(10)
        for column, axis in enumerate(("X", "Y", "Z")):
            axis_grid.addWidget(self._build_axis_card(axis), 0, column)
        self.root.addLayout(axis_grid, 3)

        lower = QHBoxLayout()
        lower.setSpacing(10)
        lower.addWidget(self._build_vacuum_card(), 2)
        lower.addWidget(self._build_conveyor_card(), 2)
        lower.addWidget(self._build_mode_card(), 2)
        self.root.addLayout(lower, 2)

        interlock_body = QWidget()
        interlock_layout = QHBoxLayout(interlock_body)
        interlock_layout.setContentsMargins(0, 0, 0, 0)
        self.interlocks = {
            "manual": StatusLed("Cho phép manual"),
            "safety": StatusLed("Safety OK"),
            "homed": StatusLed("Axes Homed"),
            "servo": StatusLed("Servo sẵn sàng"),
            "fault": StatusLed("Không có lỗi"),
        }
        for led in self.interlocks.values():
            interlock_layout.addWidget(led)
        self.root.addWidget(SectionCard("TRẠNG THÁI / LIÊN ĐỘNG AN TOÀN", interlock_body, title_icon="⚙"))
        self.refresh()

    def _build_axis_card(self, axis: str) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        pos_caption = QLabel("Vị trí hiện tại (mm)")
        pos_caption.setObjectName("muted")
        value = QLabel("+000.00")
        value.setObjectName("metricValue")
        value.setStyleSheet("font-family:Consolas; font-size:32px;")
        self.axis_labels[axis.lower()] = value
        layout.addWidget(pos_caption)
        layout.addWidget(value)

        jog_row = QHBoxLayout()
        minus = QPushButton("−\nJOG -")
        plus = QPushButton("+\nJOG +")
        minus.setObjectName("manualButton")
        plus.setObjectName("manualButton")
        minus.clicked.connect(lambda checked=False, a=axis.lower(): self._jog(a, -1.0))
        plus.clicked.connect(lambda checked=False, a=axis.lower(): self._jog(a, 1.0))
        jog_row.addWidget(minus)
        jog_row.addWidget(plus)
        layout.addLayout(jog_row)

        home = QPushButton("⌂  HOME AXIS")
        home.clicked.connect(lambda checked=False, a=axis.lower(): self.context.plc.home_axis(a))
        layout.addWidget(home)

        step_caption = QLabel("BƯỚC DI CHUYỂN")
        step_caption.setObjectName("muted")
        layout.addWidget(step_caption)
        step_row = QHBoxLayout()
        group = QButtonGroup(body)
        group.setExclusive(True)
        for step in (1, 5, 10):
            radio = QRadioButton(f"{step} mm")
            radio.setProperty("stepValue", step)
            if step == 1:
                radio.setChecked(True)
            radio.toggled.connect(lambda checked, s=step: self._set_step(s) if checked else None)
            group.addButton(radio)
            step_row.addWidget(radio)
        layout.addLayout(step_row)
        return SectionCard(f"TRỤC {axis}", body, title_icon="↔" if axis == "X" else "↕")

    def _build_vacuum_card(self) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        self.vacuum_led = StatusLed("TẮT")
        layout.addWidget(self.vacuum_led)
        buttons = QHBoxLayout()
        on = QPushButton("▶  BẬT")
        off = QPushButton("■  TẮT")
        on.setObjectName("positiveButton")
        off.setObjectName("negativeButton")
        on.clicked.connect(lambda: self.context.plc.set_vacuum(True))
        off.clicked.connect(lambda: self.context.plc.set_vacuum(False))
        buttons.addWidget(on)
        buttons.addWidget(off)
        layout.addLayout(buttons)
        return SectionCard("VACUUM (HÚT CHÂN KHÔNG)", body, title_icon="◉")

    def _build_conveyor_card(self) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        self.conveyor_led = StatusLed("DỪNG")
        layout.addWidget(self.conveyor_led)
        buttons = QHBoxLayout()
        run = QPushButton("▶  CHẠY")
        stop = QPushButton("■  DỪNG")
        run.setObjectName("positiveButton")
        stop.setObjectName("negativeButton")
        run.clicked.connect(lambda: self.context.plc.set_conveyor(True))
        stop.clicked.connect(lambda: self.context.plc.set_conveyor(False))
        buttons.addWidget(run)
        buttons.addWidget(stop)
        layout.addLayout(buttons)
        return SectionCard("BĂNG TẢI", body, title_icon="▰")

    def _build_mode_card(self) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        self.mode_label = QLabel("MODE: --")
        self.mode_label.setObjectName("metricValue")
        layout.addWidget(self.mode_label)
        to_manual = QPushButton("CHUYỂN MANUAL")
        to_auto = QPushButton("CHUYỂN AUTO")
        to_manual.clicked.connect(lambda: self.context.plc.set_mode("MANUAL"))
        to_auto.clicked.connect(lambda: self.context.plc.set_mode("AUTO"))
        layout.addWidget(to_manual)
        layout.addWidget(to_auto)
        return SectionCard("CHẾ ĐỘ ĐIỀU KHIỂN", body, title_icon="⚙")

    def _set_step(self, step: float) -> None:
        self.step_mm = float(step)

    def _jog(self, axis: str, direction: float) -> None:
        self.context.plc.jog(axis, direction * self.step_mm)
        self.refresh()

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        for key in ("x", "y", "z"):
            value = getattr(status.axes, key)
            self.axis_labels[key].setText(f"{value:+07.2f}")

        self.vacuum_led.set_text("BẬT" if status.vacuum_on else "TẮT")
        self.vacuum_led.set_active(status.vacuum_on)
        self.conveyor_led.set_text("CHẠY" if status.conveyor_on else "DỪNG")
        self.conveyor_led.set_active(status.conveyor_on)
        self.mode_label.setText(f"MODE: {status.mode.value}")

        manual = status.mode == MachineMode.MANUAL
        self.interlocks["manual"].set_active(manual)
        self.interlocks["safety"].set_active(status.safety_ok, fault=not status.safety_ok)
        self.interlocks["homed"].set_active(status.axis_homed)
        self.interlocks["servo"].set_active(status.servo_ready)
        self.interlocks["fault"].set_active(status.fault_code == 0, fault=status.fault_code != 0)
