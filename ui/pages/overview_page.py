from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from ui.pages.base_page import BasePage
from ui.widgets import CameraView, CounterRow, MetricValue, SectionCard, StatusLed


class OverviewPage(BasePage):
    """Màn hình tổng quan gần bố cục mockup nhưng chỉ hiển thị dữ liệu có thật.

    Phần cứng hiện chưa có encoder băng tải và cảm biến áp suất/vacuum feedback,
    vì vậy HMI chỉ hiển thị command/output state cho các phần đó. Không tạo số
    tốc độ hoặc áp suất giả để làm đẹp giao diện.
    """

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH TỔNG QUAN",
            "Tổng quan trạng thái hệ thống và sản lượng trong thời gian thực",
            "⌂",
        )
        self.context = context

        # ===== HÀNG 1: PLC / CAMERA / CONVEYOR / VACUUM / MODE =====
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(12)
        top_grid.setVerticalSpacing(10)

        self.plc_card = self._device_card(
            "PLC",
            "▣",
            ("Model", "Kết nối", "Trạng thái"),
        )
        self.camera_card = self._device_card(
            "Camera",
            "▰",
            ("Nguồn", "Trạng thái", "FPS đặt"),
        )
        self.conveyor_card = self._device_card(
            "Băng tải",
            "▱",
            ("Lệnh", "Feedback", "Tốc độ thực"),
        )
        self.vacuum_card = self._device_card(
            "Hút chân không",
            "◉",
            ("Van output", "Feedback", "Áp suất"),
        )
        self.mode_card = self._mode_card()

        cards = (
            self.plc_card,
            self.camera_card,
            self.conveyor_card,
            self.vacuum_card,
            self.mode_card,
        )
        for column, card_data in enumerate(cards):
            top_grid.addWidget(card_data[0], 0, column)
            top_grid.setColumnStretch(column, 1)

        self.root.addLayout(top_grid)

        # ===== HÀNG 2: CAMERA + COUNTER + MACHINE STATUS =====
        middle = QHBoxLayout()
        middle.setSpacing(12)

        self.camera_view = CameraView("CHƯA BẬT CAMERA")
        self.camera_view.setMinimumSize(620, 360)
        self.context.camera.frame_ready.connect(self.camera_view.set_frame)
        middle.addWidget(
            SectionCard("HÌNH ẢNH CAMERA TRỰC TIẾP", self.camera_view, title_icon="▣"),
            5,
        )

        counter_body = QWidget()
        counter_layout = QVBoxLayout(counter_body)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(8)
        self.counter_rows: dict[int, CounterRow] = {}
        for color in self.context.colors.enabled():
            row = CounterRow(color.display_name, color.ui_color)
            self.counter_rows[color.id] = row
            counter_layout.addWidget(row)

        self.unknown_counter = CounterRow("Lỗi / Không xác định", "#94a3b8")
        counter_layout.addWidget(self.unknown_counter)

        total_row = QHBoxLayout()
        total_title = QLabel("Tổng sản lượng")
        total_title.setObjectName("counterName")
        self.total_count = QLabel("0000")
        self.total_count.setObjectName("totalCounterValue")
        self.total_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_row.addWidget(total_title, 1)
        total_row.addWidget(self.total_count)
        counter_layout.addSpacing(5)
        counter_layout.addLayout(total_row)
        counter_layout.addStretch()

        middle.addWidget(
            SectionCard("THỐNG KÊ SẢN PHẨM", counter_body, title_icon="▥"),
            3,
        )

        status_body = QWidget()
        status_layout = QVBoxLayout(status_body)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        self.ready_leds = {
            "mode": StatusLed("AUTO sẵn sàng"),
            "plc": StatusLed("PLC kết nối"),
            "camera": StatusLed("Camera Online"),
            "homed": StatusLed("Các trục đã Home"),
            "safety": StatusLed("Liên động an toàn OK"),
            "fault": StatusLed("Không có lỗi hệ thống"),
        }
        for led in self.ready_leds.values():
            status_layout.addWidget(led)
        status_layout.addStretch()

        middle.addWidget(
            SectionCard("TRẠNG THÁI MÁY", status_body, title_icon="⚙"),
            3,
        )
        self.root.addLayout(middle, 1)

        # ===== HÀNG 3: AXIS + ALARM TABLE =====
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        axis_body = QWidget()
        axis_layout = QVBoxLayout(axis_body)
        axis_layout.setContentsMargins(0, 0, 0, 0)
        axis_layout.setSpacing(8)

        axis_values = QHBoxLayout()
        axis_values.setSpacing(10)
        self.axis_metrics = {
            "x": MetricValue("Trục X", "0.00", "mm"),
            "y": MetricValue("Trục Y", "0.00", "mm"),
            "z": MetricValue("Trục Z", "0.00", "mm"),
        }
        for metric in self.axis_metrics.values():
            axis_values.addWidget(metric, 1)
        axis_layout.addLayout(axis_values)

        axis_note = QLabel(
            "Tọa độ theo PLC sau Homing (open-loop); chưa có encoder phản hồi vị trí độc lập."
        )
        axis_note.setObjectName("muted")
        axis_note.setWordWrap(True)
        axis_layout.addWidget(axis_note)

        bottom.addWidget(
            SectionCard("VỊ TRÍ TRỤC THEO PLC", axis_body, title_icon="⌖"),
            4,
        )

        alarm_body = QWidget()
        alarm_layout = QVBoxLayout(alarm_body)
        alarm_layout.setContentsMargins(0, 0, 0, 0)
        alarm_layout.setSpacing(6)
        alarm_hint = QLabel("Không có cảnh báo gần đây")
        alarm_hint.setObjectName("muted")
        alarm_layout.addWidget(alarm_hint)

        self.alarm_table = QTableWidget(0, 4)
        self.alarm_table.setHorizontalHeaderLabels(["Thời gian", "Mức độ", "Mã lỗi", "Nội dung"])
        self.alarm_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.alarm_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.alarm_table.verticalHeader().setVisible(False)
        self.alarm_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.alarm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.alarm_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.alarm_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.alarm_table.setMinimumHeight(96)
        alarm_layout.addWidget(self.alarm_table, 1)

        bottom.addWidget(
            SectionCard("CẢNH BÁO GẦN ĐÂY", alarm_body, title_icon="⚠"),
            5,
        )
        self.root.addLayout(bottom)

        self.refresh()

    def _device_card(
        self,
        title: str,
        icon: str,
        field_names: tuple[str, str, str],
    ) -> tuple[SectionCard, StatusLed, dict[str, QLabel]]:
        """Tạo card thiết bị có LED trạng thái và ba dòng thông tin."""
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        led = StatusLed("Đang kiểm tra")
        layout.addWidget(led)

        values: dict[str, QLabel] = {}
        for field_name in field_names:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            label = QLabel(field_name)
            label.setObjectName("deviceFieldName")
            value = QLabel("--")
            value.setObjectName("deviceFieldValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(value)
            layout.addLayout(row)
            values[field_name] = value

        layout.addStretch()
        card = SectionCard(title, body, title_icon=icon)
        card.setMinimumHeight(178)
        return card, led, values

    def _mode_card(self) -> tuple[SectionCard, StatusLed, dict[str, QLabel]]:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.mode_badge = QLabel("AUTO")
        self.mode_badge.setObjectName("modeBadge")
        self.mode_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_badge)

        led = StatusLed("Đang kiểm tra")
        layout.addWidget(led)

        values: dict[str, QLabel] = {}
        for field_name in ("Trạng thái", "Chu trình", "Fault"):
            row = QHBoxLayout()
            label = QLabel(field_name)
            label.setObjectName("deviceFieldName")
            value = QLabel("--")
            value.setObjectName("deviceFieldValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(value)
            layout.addLayout(row)
            values[field_name] = value

        card = SectionCard("Chế độ máy", body, title_icon="⚙")
        card.setMinimumHeight(178)
        return card, led, values

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        plc_driver = str(self.context.config.get("plc.driver", "mock")).strip().lower()
        is_mock = plc_driver == "mock"

        # PLC
        _, plc_led, plc = self.plc_card
        plc_led.set_text("Mô phỏng" if is_mock else ("Đang hoạt động" if status.connected else "Mất kết nối"))
        plc_led.set_active(status.connected, fault=not status.connected)
        plc["Model"].setText("S7-1200 (MOCK)" if is_mock else "S7-1200")
        plc["Kết nối"].setText("Mô phỏng" if is_mock else ("Đã kết nối" if status.connected else "Offline"))
        plc["Trạng thái"].setText(status.state.value)

        # Camera: FPS ở đây là setpoint cấu hình, chưa phải FPS đo thực tế.
        _, camera_led, camera = self.camera_card
        camera_led.set_text("Đang hoạt động" if self.context.camera.running else "Offline")
        camera_led.set_active(self.context.camera.running)
        camera["Nguồn"].setText(str(self.context.config.get("camera.source", 0)))
        camera["Trạng thái"].setText("Online" if self.context.camera.running else "Offline")
        camera["FPS đặt"].setText(str(self.context.config.get("camera.fps", 30)))

        # Không có encoder băng tải: chỉ biết command/output state.
        _, conveyor_led, conveyor = self.conveyor_card
        conveyor_led.set_text("Lệnh RUN" if status.conveyor_on else "Lệnh STOP")
        conveyor_led.set_active(status.conveyor_on)
        conveyor["Lệnh"].setText("RUN" if status.conveyor_on else "STOP")
        conveyor["Feedback"].setText("Không trang bị")
        conveyor["Tốc độ thực"].setText("Không đo")

        # Không có pressure sensor hoặc vacuum switch: chỉ biết output van.
        _, vacuum_led, vacuum = self.vacuum_card
        vacuum_led.set_text("Van ON" if status.vacuum_on else "Van OFF")
        vacuum_led.set_active(status.vacuum_on)
        vacuum["Van output"].setText("ON" if status.vacuum_on else "OFF")
        vacuum["Feedback"].setText("Không trang bị")
        vacuum["Áp suất"].setText("Không đo")

        # Mode / cycle
        _, mode_led, mode = self.mode_card
        self.mode_badge.setText(status.mode.value)
        mode_led.set_text("Sẵn sàng" if status.fault_code == 0 else "Có lỗi")
        mode_led.set_active(status.connected and status.fault_code == 0, fault=status.fault_code != 0)
        mode["Trạng thái"].setText(status.state.value)
        mode["Chu trình"].setText("Tự động" if status.mode.value == "AUTO" else "Điều khiển tay")
        mode["Fault"].setText(str(status.fault_code) if status.fault_code else "Không")

        # Axis position: PLC-calculated position, không encoder feedback.
        self.axis_metrics["x"].set_value(f"{status.axes.x:.2f}")
        self.axis_metrics["y"].set_value(f"{status.axes.y:.2f}")
        self.axis_metrics["z"].set_value(f"{status.axes.z:.2f}")

        # Readiness dùng tín hiệu HMI thực sự có thể biết.
        self.ready_leds["mode"].set_text(f"{status.mode.value} sẵn sàng")
        self.ready_leds["mode"].set_active(status.mode.value == "AUTO" and status.fault_code == 0)
        self.ready_leds["plc"].set_active(status.connected, fault=not status.connected)
        self.ready_leds["camera"].set_active(self.context.camera.running)
        self.ready_leds["homed"].set_active(status.axis_homed)
        self.ready_leds["safety"].set_active(status.safety_ok, fault=not status.safety_ok)
        self.ready_leds["fault"].set_active(status.fault_code == 0, fault=status.fault_code != 0)

        total = 0
        for color_id, row in self.counter_rows.items():
            count = self.context.state.counters.get(color_id, 0)
            row.set_count(count)
            total += count
        self.unknown_counter.set_count(self.context.state.unknown_count)
        total += self.context.state.unknown_count
        self.total_count.setText(f"{max(0, int(total)):04d}")
