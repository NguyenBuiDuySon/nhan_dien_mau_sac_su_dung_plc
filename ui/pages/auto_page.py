from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from domain.machine import MachineMode, MachineState, PLCStatus
from ui.pages.base_page import BasePage
from ui.widgets import CameraView, CounterRow, SectionCard, StatusLed


class AutoPage(BasePage):
    """Màn hình vận hành tự động.

    HMI chỉ gửi command. Trạng thái RUNNING / PAUSED / FAULT phải lấy lại
    từ PLC, không tự đổi trạng thái sau khi người dùng bấm nút.

    Bộ đếm hiện vẫn nằm trong ApplicationState phía PC. Khi hoàn thiện luồng
    PLC DONE, chỉ tăng counter sau khi PLC xác nhận phân loại hoàn tất.
    """

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH AUTO",
            "Vận hành chu trình tự động và theo dõi sản phẩm đang phân loại",
        )

        self.context = context
        self.counter_rows: dict[int, CounterRow] = {}

        self._build_content()
        self._build_controls()

        self.refresh()

    # ------------------------------------------------------------------
    # BUILD UI
    # ------------------------------------------------------------------

    def _build_content(self) -> None:
        content = QHBoxLayout()
        content.setSpacing(12)

        # ==============================================================
        # LEFT: CAMERA
        # ==============================================================

        self.camera_view = CameraView("CAMERA OFFLINE")
        self.camera_view.setMinimumSize(760, 460)

        self.context.camera.frame_ready.connect(
            self.camera_view.set_frame
        )

        content.addWidget(
            SectionCard(
                "HÌNH ẢNH CAMERA TRỰC TIẾP",
                self.camera_view,
            ),
            5,
        )

        # ==============================================================
        # RIGHT
        # ==============================================================

        right = QVBoxLayout()
        right.setSpacing(12)

        right.addWidget(
            self._build_counter_card(),
            3,
        )

        right.addWidget(
            self._build_classification_card(),
            2,
        )

        content.addLayout(
            right,
            2,
        )

        self.root.addLayout(
            content,
            1,
        )

    def _build_counter_card(self) -> SectionCard:
        """Danh sách màu cuộn được, tổng sản lượng luôn cố định."""

        body = QWidget()

        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # Header + nút xóa bộ đếm.
        top = QHBoxLayout()

        color_title = QLabel("Màu sắc")
        color_title.setObjectName("counterTableHeader")

        count_title = QLabel("Số lượng")
        count_title.setObjectName("counterTableHeader")

        self.clear_counter_btn = QPushButton(
            "Xóa bộ đếm"
        )
        self.clear_counter_btn.setObjectName(
            "counterResetButton"
        )
        self.clear_counter_btn.clicked.connect(
            self._confirm_reset_counters
        )

        top.addWidget(
            color_title,
            1,
        )

        top.addWidget(
            count_title,
        )

        top.addWidget(
            self.clear_counter_btn,
        )

        root.addLayout(top)

        # Scroll list.
        self.counter_scroll = QScrollArea()
        self.counter_scroll.setObjectName(
            "counterScroll"
        )
        self.counter_scroll.setWidgetResizable(
            True
        )

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

        # Total không nằm trong scroll.
        separator = QFrame()
        separator.setFrameShape(
            QFrame.Shape.HLine
        )
        separator.setObjectName(
            "sectionLine"
        )

        root.addWidget(separator)

        total = QHBoxLayout()

        total_label = QLabel(
            "Tổng sản lượng"
        )
        total_label.setObjectName(
            "totalCounterTitle"
        )

        self.total_count = QLabel(
            "0000"
        )
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
            "BỘ ĐẾM SẢN PHẨM",
            body,
        )

    def _build_classification_card(
        self,
    ) -> SectionCard:
        """Thông tin sản phẩm và chu trình hiện tại."""

        body = QWidget()

        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.classification_values: dict[str, QLabel] = {}

        self._add_info_row(
            layout,
            "Màu đang xử lý",
            "color",
        )

        self._add_info_row(
            layout,
            "Vị trí thả",
            "destination",
        )

        self._add_info_row(
            layout,
            "Độ tin cậy HSV",
            "confidence",
        )

        self._add_info_row(
            layout,
            "Trạng thái chu trình",
            "cycle",
        )

        sensor_row = QHBoxLayout()

        sensor_name = QLabel(
            "Cảm biến sản phẩm"
        )
        sensor_name.setObjectName(
            "classificationLabel"
        )

        self.product_sensor_led = StatusLed(
            "Không có sản phẩm"
        )

        sensor_row.addWidget(
            sensor_name,
            1,
        )

        sensor_row.addWidget(
            self.product_sensor_led,
        )

        layout.addLayout(sensor_row)
        layout.addStretch()

        card = SectionCard(
            "THÔNG TIN PHÂN LOẠI",
            body,
        )

        card.setMinimumHeight(250)

        return card

    def _add_info_row(
        self,
        parent_layout: QVBoxLayout,
        label_text: str,
        key: str,
    ) -> None:
        row = QHBoxLayout()

        name = QLabel(label_text)
        name.setObjectName(
            "classificationLabel"
        )

        value = QLabel("--")
        value.setObjectName(
            "classificationValue"
        )

        value.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        row.addWidget(
            name,
            1,
        )

        row.addWidget(
            value,
        )

        parent_layout.addLayout(row)

        self.classification_values[key] = value

    def _build_controls(self) -> None:
        """Hàng nút điều khiển chính của chế độ Auto."""

        controls = QGridLayout()
        controls.setHorizontalSpacing(12)

        self.start_btn = QPushButton(
            "START\nBắt đầu chạy"
        )
        self.start_btn.setObjectName(
            "startButton"
        )

        self.pause_btn = QPushButton(
            "PAUSE\nTạm dừng"
        )
        self.pause_btn.setObjectName(
            "pauseButton"
        )

        self.stop_btn = QPushButton(
            "STOP\nDừng hệ thống"
        )
        self.stop_btn.setObjectName(
            "stopButton"
        )

        self.reset_btn = QPushButton(
            "RESET LỖI\nKhôi phục trạng thái"
        )
        self.reset_btn.setObjectName(
            "resetButton"
        )

        buttons = (
            self.start_btn,
            self.pause_btn,
            self.stop_btn,
            self.reset_btn,
        )

        for column, button in enumerate(
            buttons
        ):
            controls.addWidget(
                button,
                0,
                column,
            )

            controls.setColumnStretch(
                column,
                1,
            )

        self.root.addLayout(
            controls,
        )

        self.start_btn.clicked.connect(
            self.context.plc.start_auto
        )

        self.pause_btn.clicked.connect(
            self.context.plc.pause_auto
        )

        self.stop_btn.clicked.connect(
            self.context.plc.stop
        )

        self.reset_btn.clicked.connect(
            self.context.plc.reset
        )

    # ------------------------------------------------------------------
    # COUNTER
    # ------------------------------------------------------------------

    def _rebuild_counter_rows(self) -> None:
        while self.counter_list_layout.count():
            item = self.counter_list_layout.takeAt(
                0
            )

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

            self.counter_rows[
                color.id
            ] = row

            self.counter_list_layout.addWidget(
                row
            )

        self.unknown_counter = CounterRow(
            "Lỗi / Không xác định",
            "#94a3b8",
        )

        self.counter_list_layout.addWidget(
            self.unknown_counter
        )

        self.counter_list_layout.addStretch()

    def _sync_counter_structure(self) -> None:
        enabled_ids = {
            color.id
            for color
            in self.context.colors.enabled()
        }

        if enabled_ids != set(
            self.counter_rows
        ):
            self._rebuild_counter_rows()

    def _confirm_reset_counters(
        self,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Xóa bộ đếm",
            (
                "Bạn có chắc muốn xóa toàn bộ "
                "bộ đếm sản phẩm?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.context.state.reset_counters()

        self.refresh()

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        status = self.context.plc.get_status()

        self._refresh_buttons(status)
        self._refresh_classification(status)
        self._refresh_counters()


    def _refresh_buttons(
        self,
        status: PLCStatus,
    ) -> None:
        """Enable nút theo trạng thái PLC thực."""

        can_start = (
            status.connected
            and status.mode == MachineMode.AUTO
            and status.state
            in {
                MachineState.READY,
                MachineState.PAUSED,
            }
            and status.axis_homed
            and status.fault_code == 0
        )

        self.start_btn.setEnabled(can_start)

        self.pause_btn.setEnabled(
            status.connected
            and status.state == MachineState.RUNNING
        )

        self.stop_btn.setEnabled(status.connected)
        self.reset_btn.setEnabled(status.connected)


    def _refresh_classification(
        self,
        status: PLCStatus,
    ) -> None:
        color_label = self.classification_values["color"]
        destination_label = self.classification_values["destination"]
        confidence_label = self.classification_values["confidence"]
        cycle_label = self.classification_values["cycle"]

        detection = self.context.state.current_detection

    # phần còn lại giữ nguyên...

        # --------------------------------------------------------------
        # Vision result
        # --------------------------------------------------------------

        if detection is None:
            color_label.setText("--")
            destination_label.setText("--")
            confidence_label.setText("--")

        elif detection.color_id is None:
            color_label.setText(
                "Không xác định"
            )

            destination_label.setText(
                "Hàng lỗi"
            )

            confidence_label.setText(
                f"{detection.confidence * 100:.0f} %"
            )

        else:
            try:
                color = self.context.colors.get(
                    detection.color_id
                )

                color_label.setText(
                    color.display_name
                )
            except KeyError:
                color_label.setText(
                    f"ID {detection.color_id}"
                )

            confidence_label.setText(
                f"{detection.confidence * 100:.0f} %"
            )

            # Chỉ resolve khi đã chốt màu ổn định.
            if detection.stable:
                try:
                    destination = (
                        self.context.routing_service.resolve(
                            detection.color_id
                        )
                    )

                    destination_label.setText(
                        destination.display_name
                    )

                except (
                    KeyError,
                    LookupError,
                    ValueError,
                ):
                    destination_label.setText(
                        "Chưa cấu hình"
                    )

            else:
                destination_label.setText(
                    "Đang xác nhận"
                )

        # --------------------------------------------------------------
        # PLC cycle
        # --------------------------------------------------------------

        cycle_label.setText(
            self._cycle_text(
                status.state
            )
        )

        # --------------------------------------------------------------
        # Product sensor
        # --------------------------------------------------------------

        if status.product_sensor:
            self.product_sensor_led.set_text(
                "Có sản phẩm"
            )

            self.product_sensor_led.set_active(
                True
            )

        else:
            self.product_sensor_led.set_text(
                "Không có sản phẩm"
            )

            self.product_sensor_led.set_active(
                False
            )

    def _refresh_counters(self) -> None:
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

            row.set_count(
                count
            )

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

    @staticmethod
    def _cycle_text(
        state: MachineState,
    ) -> str:
        labels = {
            MachineState.IDLE: "Chờ",
            MachineState.READY: "Sẵn sàng",
            MachineState.RUNNING: "Đang phân loại",
            MachineState.PAUSED: "Tạm dừng",
            MachineState.HOMING: "Đang Home",
            MachineState.FAULT: "Có lỗi",
        }

        return labels.get(
            state,
            state.value,
        )