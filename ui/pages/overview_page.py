from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from ui.pages.base_page import BasePage
from ui.widgets import CameraView, CounterRow, MetricValue, SectionCard, StatusLed


class OverviewPage(BasePage):
    """Màn hình tổng quan.

    Mục đích:
    - Xem nhanh trạng thái PLC, Camera, băng tải và van hút.
    - Quan sát camera trực tiếp.
    - Xem sản lượng phân loại.
    - Xem tọa độ X/Y/Z do PLC quản lý.

    Không hiển thị:
    - tốc độ băng tải thực vì hệ thống không có encoder;
    - áp suất hút vì hệ thống không có cảm biến áp suất;
    - trạng thái giả hoặc dữ liệu mô phỏng.
    """

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH TỔNG QUAN",
            "Tổng quan trạng thái hệ thống và sản lượng trong thời gian thực",
        )

        self.context = context

        # Counter được sinh động từ colors.json.
        self.counter_rows: dict[int, CounterRow] = {}

        self._build_device_row()
        self._build_main_content()

        self.refresh()

    # ------------------------------------------------------------------
    # BUILD UI
    # ------------------------------------------------------------------

    def _build_device_row(self) -> None:
        """Hàng trên cùng: PLC / Camera / Băng tải / Vacuum."""

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(0)

        self.plc_card = self._device_card(
            "PLC",
            (
                "Model",
                "Kết nối",
                "Trạng thái máy",
            ),
        )

        # Theo yêu cầu: FPS nằm trước trạng thái.
        self.camera_card = self._device_card(
            "Camera",
            (
                "Nguồn",
                "FPS",
                "Trạng thái",
            ),
        )

        # Không có encoder nên không hiển thị tốc độ thực.
        self.conveyor_card = self._device_card(
            "Băng tải",
            (
                "Lệnh PLC",
                "Output",
                "Trạng thái",
            ),
        )

        # Không có pressure sensor nên không hiển thị áp suất.
        self.vacuum_card = self._device_card(
            "Hút chân không",
            (
                "Van điện từ",
                "Output PLC",
                "Trạng thái",
            ),
        )

        cards = (
            self.plc_card,
            self.camera_card,
            self.conveyor_card,
            self.vacuum_card,
        )

        for column, card_data in enumerate(cards):
            grid.addWidget(card_data[0], 0, column)
            grid.setColumnStretch(column, 1)

        self.root.addLayout(grid)

    def _build_main_content(self) -> None:
        """Camera + vị trí trục bên trái, bộ đếm bên phải."""

        content = QHBoxLayout()
        content.setSpacing(12)

        # ==============================================================
        # LEFT: CAMERA + AXIS POSITION
        # ==============================================================

        left = QVBoxLayout()
        left.setSpacing(12)

        self.camera_view = CameraView("CHƯA BẬT CAMERA")
        self.camera_view.setMinimumSize(720, 400)

        self.context.camera.frame_ready.connect(
            self.camera_view.set_frame
        )

        camera_card = SectionCard(
            "HÌNH ẢNH CAMERA TRỰC TIẾP",
            self.camera_view,
        )

        left.addWidget(camera_card, 5)

        axis_card = self._build_axis_card()
        left.addWidget(axis_card, 1)

        content.addLayout(left, 5)

        # ==============================================================
        # RIGHT: PRODUCT COUNTER
        # ==============================================================

        counter_card = self._build_counter_card()
        content.addWidget(counter_card, 2)

        self.root.addLayout(content, 1)

    def _build_axis_card(self) -> SectionCard:
        """Hiển thị vị trí PLC đang quản lý cho X/Y/Z."""

        body = QWidget()

        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.axis_metrics = {
            "x": MetricValue(
                "Trục X",
                "0.00",
                "mm",
            ),
            "y": MetricValue(
                "Trục Y",
                "0.00",
                "mm",
            ),
            "z": MetricValue(
                "Trục Z",
                "0.00",
                "mm",
            ),
        }

        for metric in self.axis_metrics.values():
            layout.addWidget(metric, 1)

        card = SectionCard(
            "VỊ TRÍ TRỤC THEO PLC",
            body,
        )

        card.setMinimumHeight(155)
        card.setMaximumHeight(175)

        return card

    def _build_counter_card(self) -> SectionCard:
        """Bộ đếm động.

        Danh sách màu có thể cuộn.
        Tổng sản lượng nằm ngoài vùng scroll để luôn nhìn thấy.
        """

        body = QWidget()

        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # --------------------------------------------------------------
        # Header nhỏ
        # --------------------------------------------------------------

        header = QHBoxLayout()

        color_title = QLabel("Màu sắc")
        color_title.setObjectName("counterTableHeader")

        count_title = QLabel("Số lượng")
        count_title.setObjectName("counterTableHeader")
        count_title.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        header.addWidget(color_title, 1)
        header.addWidget(count_title)

        root.addLayout(header)

        # --------------------------------------------------------------
        # Scroll area
        # --------------------------------------------------------------

        self.counter_scroll = QScrollArea()
        self.counter_scroll.setObjectName("counterScroll")
        self.counter_scroll.setWidgetResizable(True)

        self.counter_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.counter_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.counter_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.counter_container = QWidget()

        self.counter_list_layout = QVBoxLayout(
            self.counter_container
        )

        self.counter_list_layout.setContentsMargins(
            0,
            0,
            4,
            0,
        )

        self.counter_list_layout.setSpacing(3)

        self.counter_scroll.setWidget(
            self.counter_container
        )

        root.addWidget(
            self.counter_scroll,
            1,
        )

        # --------------------------------------------------------------
        # Total - KHÔNG nằm trong scroll
        # --------------------------------------------------------------

        separator = QFrame()
        separator.setFrameShape(
            QFrame.Shape.HLine
        )
        separator.setObjectName("sectionLine")

        root.addWidget(separator)

        total = QHBoxLayout()

        total_label = QLabel("Tổng sản lượng")
        total_label.setObjectName("totalCounterTitle")

        self.total_count = QLabel("0000")
        self.total_count.setObjectName(
            "totalCounterValue"
        )

        self.total_count.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        total.addWidget(
            total_label,
            1,
        )

        total.addWidget(
            self.total_count,
        )

        root.addLayout(total)

        self._rebuild_counter_rows()

        return SectionCard(
            "THỐNG KÊ SẢN PHẨM",
            body,
        )

    # ------------------------------------------------------------------
    # COUNTER
    # ------------------------------------------------------------------

    def _rebuild_counter_rows(self) -> None:
        """Tạo lại danh sách CounterRow từ colors.json."""

        while self.counter_list_layout.count():
            item = self.counter_list_layout.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.counter_rows.clear()

        for color in self.context.colors.enabled():
            row = CounterRow(
                color.display_name,
                color.ui_color,
            )

            self.counter_rows[color.id] = row

            self.counter_list_layout.addWidget(
                row
            )

        # Unknown/Error luôn có một hàng riêng.
        self.unknown_counter = CounterRow(
            "Lỗi / Không xác định",
            "#94a3b8",
        )

        self.counter_list_layout.addWidget(
            self.unknown_counter
        )

        self.counter_list_layout.addStretch()

    def _sync_counter_structure(self) -> None:
        """Nếu danh sách màu thay đổi thì tự rebuild UI.

        Sau này Add/Delete/Disable màu trong popup Vision sẽ không cần
        hard-code lại Overview.
        """

        enabled_ids = {
            color.id
            for color in self.context.colors.enabled()
        }

        current_ids = set(
            self.counter_rows.keys()
        )

        if enabled_ids != current_ids:
            self._rebuild_counter_rows()

    # ------------------------------------------------------------------
    # DEVICE CARD
    # ------------------------------------------------------------------

    @staticmethod
    def _device_card(
        title: str,
        field_names: tuple[str, ...],
    ) -> tuple[
        SectionCard,
        StatusLed,
        dict[str, QLabel],
    ]:
        """Tạo card trạng thái thiết bị."""

        body = QWidget()

        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        led = StatusLed("Đang kiểm tra")
        layout.addWidget(led)

        values: dict[str, QLabel] = {}

        for field_name in field_names:
            row = QHBoxLayout()
            row.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            label = QLabel(field_name)
            label.setObjectName(
                "deviceFieldName"
            )

            value = QLabel("--")
            value.setObjectName(
                "deviceFieldValue"
            )

            value.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(value)

            layout.addLayout(row)

            values[field_name] = value

        layout.addStretch()

        card = SectionCard(
            title,
            body,
        )

        card.setMinimumHeight(168)

        return (
            card,
            led,
            values,
        )

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Đồng bộ giao diện từ trạng thái thực của PLC và Camera."""

        status = self.context.plc.get_status()

        # ==============================================================
        # PLC
        # ==============================================================

        _, plc_led, plc = self.plc_card

        if status.connected:
            plc_led.set_text("Đang hoạt động")
            plc_led.set_active(True)

            plc["Kết nối"].setText(
                "Đã kết nối"
            )
        else:
            plc_led.set_text("Mất kết nối")
            plc_led.set_active(
                False,
                fault=True,
            )

            plc["Kết nối"].setText(
                "Offline"
            )

        plc["Model"].setText(
            "S7-1200"
        )

        plc["Trạng thái máy"].setText(
            status.state.value
        )

        # ==============================================================
        # CAMERA
        # ==============================================================

        _, camera_led, camera = self.camera_card

        camera_running = (
            self.context.camera.running
        )

        if camera_running:
            camera_led.set_text(
                "Đang hoạt động"
            )

            camera_led.set_active(True)
        else:
            camera_led.set_text(
                "Offline"
            )

            camera_led.set_active(False)

        camera["Nguồn"].setText(
            str(
                self.context.config.get(
                    "camera.source",
                    0,
                )
            )
        )

        # Hiện tại đây là FPS cấu hình.
        # Khi CameraService có đo FPS thực thì đổi sang measured_fps.
        camera["FPS"].setText(
            str(
                self.context.config.get(
                    "camera.fps",
                    30,
                )
            )
        )

        camera["Trạng thái"].setText(
            "Online"
            if camera_running
            else "Offline"
        )

        # ==============================================================
        # CONVEYOR
        # ==============================================================

        _, conveyor_led, conveyor = (
            self.conveyor_card
        )

        if status.conveyor_on:
            conveyor_led.set_text(
                "Đang chạy"
            )

            conveyor_led.set_active(True)
        else:
            conveyor_led.set_text(
                "Đang dừng"
            )

            conveyor_led.set_active(False)

        conveyor["Lệnh PLC"].setText(
            "RUN"
            if status.conveyor_on
            else "STOP"
        )

        conveyor["Output"].setText(
            "ON"
            if status.conveyor_on
            else "OFF"
        )

        conveyor["Trạng thái"].setText(
            "Đang chạy"
            if status.conveyor_on
            else "Dừng"
        )

        # ==============================================================
        # VACUUM
        # ==============================================================

        _, vacuum_led, vacuum = (
            self.vacuum_card
        )

        if status.vacuum_on:
            vacuum_led.set_text(
                "Đang bật"
            )

            vacuum_led.set_active(True)
        else:
            vacuum_led.set_text(
                "Đang tắt"
            )

            vacuum_led.set_active(False)

        vacuum["Van điện từ"].setText(
            "ON"
            if status.vacuum_on
            else "OFF"
        )

        vacuum["Output PLC"].setText(
            "ON"
            if status.vacuum_on
            else "OFF"
        )

        vacuum["Trạng thái"].setText(
            "Hút"
            if status.vacuum_on
            else "Tắt"
        )

        # ==============================================================
        # AXIS POSITION
        # ==============================================================

        self.axis_metrics["x"].set_value(
            f"{status.axes.x:.2f}"
        )

        self.axis_metrics["y"].set_value(
            f"{status.axes.y:.2f}"
        )

        self.axis_metrics["z"].set_value(
            f"{status.axes.z:.2f}"
        )

        # ==============================================================
        # PRODUCT COUNTER
        # ==============================================================

        self._sync_counter_structure()

        total = 0

        for color_id, row in (
            self.counter_rows.items()
        ):
            count = (
                self.context.state.counters.get(
                    color_id,
                    0,
                )
            )

            row.set_count(count)

            total += count

        unknown_count = (
            self.context.state.unknown_count
        )

        self.unknown_counter.set_count(
            unknown_count
        )

        total += unknown_count

        self.total_count.setText(
            f"{max(0, int(total)):04d}"
        )