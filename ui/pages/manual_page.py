from __future__ import annotations

from typing import TypedDict

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from domain.destination import Destination
from domain.machine import MachineMode, PLCStatus
from ui.pages.base_page import BasePage
from ui.widgets import SectionCard, StatusLed


class AxisControls(TypedDict):
    max_mm: QLineEdit
    velocity_mm_s: QLineEdit
    position_mm: QLabel
    jog_step_mm: QLineEdit
    jog_minus: QPushButton
    jog_plus: QPushButton
    home: QPushButton


class ManualPage(BasePage):
    """Manual HMI: commissioning trục + output + Color -> Destination.

    Quy ước V04:
    - Home của X/Y/Z = 0 mm.
    - HMI làm việc bằng mm.
    - Min cố định 0 mm; Max/Velocity/Jog Step nhập trực tiếp bằng bàn phím.
    - Color và HSV được quản lý bên Vision.
    - Manual chỉ quản lý Color -> Destination -> XYZ.
    - PLC vẫn là nguồn trạng thái thật và lớp interlock cuối cùng.
    """

    AXES = ("x", "y", "z")

    AXIS_CELL_WIDTH = 82
    AXIS_CELL_HEIGHT = 34

    JOG_BUTTON_WIDTH = 76
    JOG_BUTTON_HEIGHT = 34

    HOME_BUTTON_WIDTH = 76
    HOME_BUTTON_HEIGHT = 34

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH MANUAL & CÀI ĐẶT",
            "Điều khiển tay, dò hành trình và quản lý vị trí phân loại",
        )

        self.context = context
        self.axis_controls: dict[str, AxisControls] = {}
        self.selected_color_id: int | None = None

        self._build_top()
        self._build_output_row()
        self._build_routing_manager()

        self._refresh_route_table()
        self.refresh()

    # ------------------------------------------------------------------
    # TOP: AXIS + PLC
    # ------------------------------------------------------------------

    def _build_top(self) -> None:
        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self._build_axis_card(), 5)
        top.addWidget(self._build_plc_connection_card(), 2)
        self.root.addLayout(top)

    def _build_axis_card(self) -> SectionCard:
        body = QWidget()
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(2)

        # Cho bảng trục trải đều chiều ngang card, nhưng giữ hàng X/Y/Z gọn.
        # Cố định theo chiều dọc để khung PLC không làm các nút bị kéo cao.
        axis_table = QWidget()
        axis_table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        grid = QGridLayout(axis_table)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(3)

        headers = (
            "Trục",
            "Min (mm)",
            "Max (mm)",
            "Vận tốc (mm/s)",
            "Vị trí PLC (mm)",
            "Bước Jog (mm)",
            "JOG -",
            "JOG +",
            "HOME",
        )

        widths = (
            64,
            self.AXIS_CELL_WIDTH,
            self.AXIS_CELL_WIDTH,
            self.AXIS_CELL_WIDTH,
            self.AXIS_CELL_WIDTH,
            self.AXIS_CELL_WIDTH,
            self.JOG_BUTTON_WIDTH,
            self.JOG_BUTTON_WIDTH,
            self.HOME_BUTTON_WIDTH,
        )

        for column, (text, width) in enumerate(zip(headers, widths, strict=True)):
            label = QLabel(text)
            label.setObjectName("axisTableHeader")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumWidth(width)
            label.setFixedHeight(24)
            grid.addWidget(label, 0, column)
            grid.setColumnMinimumWidth(column, width)
            # Phần rộng dư chia đều ra các cột (không tăng size của ô/nút).
            grid.setColumnStretch(column, 1)

        for row_index, axis in enumerate(self.AXES, start=1):
            self._add_axis_row(grid, axis, row_index)

        # Tận dụng chiều ngang card thay vì gom một bảng nhỏ ở chính giữa.
        root.addWidget(axis_table, 0, Qt.AlignmentFlag.AlignTop)

        footer = QHBoxLayout()
        footer.setSpacing(8)

        note = QLabel(
            "Min = 0 mm tại Home. Dò Max thực tế rồi chừa khoảng an toàn cơ khí."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)

        self.home_all_btn = QPushButton("HOME ALL")
        self.home_all_btn.setObjectName("secondaryBlueButton")
        self.home_all_btn.setFixedSize(100, self.AXIS_CELL_HEIGHT)
        self.home_all_btn.setStyleSheet(self._disabled_motion_button_style())
        self.home_all_btn.clicked.connect(
            lambda: self._request_home(None)
        )

        self.save_axis_btn = QPushButton("LƯU THÔNG SỐ TRỤC")
        self.save_axis_btn.setObjectName("positiveButton")
        self.save_axis_btn.setFixedHeight(self.AXIS_CELL_HEIGHT)
        self.save_axis_btn.setMinimumWidth(150)
        self.save_axis_btn.clicked.connect(self._save_axis_settings)

        footer.addWidget(note, 1)
        footer.addWidget(self.home_all_btn)
        footer.addWidget(self.save_axis_btn)
        root.addLayout(footer)
        # Phần chiều cao dư của card sẽ xuống cuối, không dãn các hàng trục.
        root.addStretch(1)

        return SectionCard("ĐIỀU KHIỂN TRỤC", body)

    @staticmethod
    def _disabled_motion_button_style() -> str:
        """Ngăn HOME hiển thị màu xanh như nút đã sẵn sàng khi PLC offline."""
        return """
            QPushButton#secondaryBlueButton:disabled {
                background-color: #173247;
                border: 1px solid #29465e;
                color: #71869b;
            }
        """

    def _add_axis_row(
        self,
        grid: QGridLayout,
        axis: str,
        row_index: int,
    ) -> None:
        axis_name = QLabel(f"Trục {axis.upper()}")
        axis_name.setObjectName("axisName")
        axis_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        min_value = QLabel("0.00")
        min_value.setObjectName("axisReadonlyValue")
        min_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        min_value.setFixedSize(self.AXIS_CELL_WIDTH, self.AXIS_CELL_HEIGHT)

        max_edit = self._float_input(
            value=float(
                self.context.config.get(
                    f"machine.axes.{axis}.max_mm",
                    500.0,
                )
            ),
            minimum=1.0,
            maximum=5000.0,
        )

        velocity_edit = self._float_input(
            value=float(
                self.context.config.get(
                    f"machine.axes.{axis}.velocity_mm_s",
                    100.0,
                )
            ),
            minimum=0.1,
            maximum=1000.0,
        )

        position = QLabel("0.00")
        position.setObjectName("axisPositionValue")
        position.setAlignment(Qt.AlignmentFlag.AlignCenter)
        position.setFixedSize(self.AXIS_CELL_WIDTH, self.AXIS_CELL_HEIGHT)

        jog_step_edit = self._float_input(
            value=float(
                self.context.config.get(
                    f"machine.axes.{axis}.jog_step_mm",
                    5.0,
                )
            ),
            minimum=0.1,
            maximum=500.0,
        )

        jog_minus = QPushButton("JOG -")
        jog_minus.setObjectName("manualButton")
        jog_minus.setFixedSize(
            self.JOG_BUTTON_WIDTH,
            self.JOG_BUTTON_HEIGHT,
        )

        jog_plus = QPushButton("JOG +")
        jog_plus.setObjectName("manualButton")
        jog_plus.setFixedSize(
            self.JOG_BUTTON_WIDTH,
            self.JOG_BUTTON_HEIGHT,
        )

        home = QPushButton("HOME")
        home.setObjectName("secondaryBlueButton")
        home.setFixedSize(
            self.HOME_BUTTON_WIDTH,
            self.HOME_BUTTON_HEIGHT,
        )
        home.setStyleSheet(self._disabled_motion_button_style())

        jog_minus.clicked.connect(
            lambda checked=False, a=axis: self._jog(a, -1.0)
        )
        jog_plus.clicked.connect(
            lambda checked=False, a=axis: self._jog(a, 1.0)
        )
        home.clicked.connect(
            lambda checked=False, a=axis: self._request_home(a)
        )

        widgets: tuple[QWidget, ...] = (
            axis_name,
            min_value,
            max_edit,
            velocity_edit,
            position,
            jog_step_edit,
            jog_minus,
            jog_plus,
            home,
        )

        for column, widget in enumerate(widgets):
            grid.addWidget(
                widget,
                row_index,
                column,
                alignment=Qt.AlignmentFlag.AlignCenter,
            )

        # 34 px theo chiều cao ô/nút, không ép row lớn hơn nội dung.
        grid.setRowMinimumHeight(row_index, self.AXIS_CELL_HEIGHT)

        self.axis_controls[axis] = {
            "max_mm": max_edit,
            "velocity_mm_s": velocity_edit,
            "position_mm": position,
            "jog_step_mm": jog_step_edit,
            "jog_minus": jog_minus,
            "jog_plus": jog_plus,
            "home": home,
        }

    def _build_plc_connection_card(self) -> SectionCard:
        """Bố trí cấu hình PLC thành 2 cột để giảm chiều cao hàng trên.

        Giữ nguyên các thuộc tính/handler để không ảnh hưởng luồng snap7.
        """
        body = QWidget()
        layout = QGridLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.plc_host = QLineEdit(
            str(self.context.config.get("plc.host", "192.168.0.10"))
        )
        self.plc_rack = self._int_input(
            int(self.context.config.get("plc.rack", 0)), 0, 7
        )
        self.plc_slot = self._int_input(
            int(self.context.config.get("plc.slot", 1)), 0, 31
        )
        self.command_db = self._int_input(
            int(self.context.config.get("plc.command_db", 100)), 1, 65535
        )
        self.status_db = self._int_input(
            int(self.context.config.get("plc.status_db", 101)), 1, 65535
        )
        self.plc_led = StatusLed("Đang kiểm tra")

        for field in (
            self.plc_host,
            self.plc_rack,
            self.plc_slot,
            self.command_db,
            self.status_db,
        ):
            field.setFixedHeight(30)

        def add_field(name: str, widget: QWidget, row: int, col: int) -> None:
            label = QLabel(name)
            label.setObjectName("deviceFieldName")
            layout.addWidget(label, row, col)
            layout.addWidget(widget, row, col + 1)

        label_ip = QLabel("Địa chỉ IP")
        label_ip.setObjectName("deviceFieldName")
        layout.addWidget(label_ip, 0, 0)
        layout.addWidget(self.plc_host, 0, 1, 1, 3)

        add_field("Rack", self.plc_rack, 1, 0)
        add_field("Slot", self.plc_slot, 1, 2)
        add_field("Command DB", self.command_db, 2, 0)
        add_field("Status DB", self.status_db, 2, 2)

        layout.addWidget(self.plc_led, 3, 0, 1, 2)

        save = QPushButton("LƯU KẾT NỐI")
        save.setObjectName("secondaryBlueButton")
        save.setFixedHeight(32)
        save.clicked.connect(self._save_plc_settings)
        layout.addWidget(save, 3, 2, 1, 2)

        note = QLabel("Đổi IP / DB cần khởi động lại HMI.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note, 4, 0, 1, 4)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        return SectionCard("KẾT NỐI PLC", body)

    # ------------------------------------------------------------------
    # OUTPUTS
    # ------------------------------------------------------------------

    def _build_output_row(self) -> None:
        outputs = QHBoxLayout()
        outputs.setSpacing(12)
        outputs.addWidget(self._build_vacuum_card(), 1)
        outputs.addWidget(self._build_conveyor_card(), 1)
        self.root.addLayout(outputs)

    def _build_vacuum_card(self) -> SectionCard:
        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.vacuum_led = StatusLed("Đang tắt")

        on_btn = QPushButton("BẬT")
        on_btn.setObjectName("positiveButton")
        off_btn = QPushButton("TẮT")
        off_btn.setObjectName("negativeButton")

        on_btn.setFixedSize(72, 34)
        off_btn.setFixedSize(72, 34)

        on_btn.clicked.connect(lambda: self.context.plc.set_vacuum(True))
        off_btn.clicked.connect(lambda: self.context.plc.set_vacuum(False))

        self.vacuum_buttons = (on_btn, off_btn)

        layout.addWidget(self.vacuum_led, 1)
        layout.addWidget(on_btn)
        layout.addWidget(off_btn)

        card = SectionCard("HÚT CHÂN KHÔNG", body)
        card.setMaximumHeight(110)
        return card

    def _build_conveyor_card(self) -> SectionCard:
        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.conveyor_led = StatusLed("Đang dừng")

        run_btn = QPushButton("CHẠY")
        run_btn.setObjectName("positiveButton")
        stop_btn = QPushButton("DỪNG")
        stop_btn.setObjectName("negativeButton")

        run_btn.setFixedSize(72, 34)
        stop_btn.setFixedSize(72, 34)

        run_btn.clicked.connect(lambda: self.context.plc.set_conveyor(True))
        stop_btn.clicked.connect(lambda: self.context.plc.set_conveyor(False))

        self.conveyor_buttons = (run_btn, stop_btn)

        layout.addWidget(self.conveyor_led, 1)
        layout.addWidget(run_btn)
        layout.addWidget(stop_btn)

        card = SectionCard("BĂNG TẢI", body)
        card.setMaximumHeight(110)
        return card

    # ------------------------------------------------------------------
    # ROUTING / DESTINATION
    # ------------------------------------------------------------------

    def _build_routing_manager(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(12)

        route_card = self._build_route_table_card()
        detail_card = self._build_route_detail_card()

        route_card.setMinimumWidth(720)
        detail_card.setMinimumWidth(500)

        row.addWidget(route_card, 3)
        row.addWidget(detail_card, 2)
        self.root.addLayout(row, 1)

    def _build_route_table_card(self) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.route_search = QLineEdit()
        self.route_search.setPlaceholderText("Tìm màu hoặc vị trí...")
        self.route_search.setFixedHeight(32)
        self.route_search.textChanged.connect(self._apply_route_filter)

        self.route_count_label = QLabel("")
        self.route_count_label.setObjectName("muted")

        toolbar.addWidget(self.route_search, 1)
        toolbar.addWidget(self.route_count_label)
        layout.addLayout(toolbar)

        self.route_table = QTableWidget(0, 6)
        self.route_table.setHorizontalHeaderLabels(
            ["Màu", "Vị trí đích", "X (mm)", "Y (mm)", "Z (mm)", "Route"]
        )
        self.route_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.route_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.route_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.route_table.setAlternatingRowColors(True)
        # Tránh hàng đang chọn chuyển sang xám sáng, khó đọc trên giao diện tối.
        self.route_table.setObjectName("routingTable")
        self.route_table.setStyleSheet("""
            QTableWidget#routingTable::item:selected {
                background-color: #12486d;
                color: #ffffff;
            }
            QTableWidget#routingTable::item:selected:!active {
                background-color: #12486d;
                color: #ffffff;
            }
        """)
        self.route_table.verticalHeader().setVisible(False)
        self.route_table.verticalHeader().setDefaultSectionSize(32)

        header = self.route_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for index in (2, 3, 4, 5):
            header.setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)

        self.route_table.currentCellChanged.connect(
            self._on_route_current_cell_changed
        )

        layout.addWidget(self.route_table, 1)
        return SectionCard("QUẢN LÝ PHÂN LOẠI", body)

    def _build_route_detail_card(self) -> SectionCard:
        body = QWidget()

        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)

        # --------------------------------------------------------------
        # Row 0: selected color
        # --------------------------------------------------------------

        color_label = QLabel("Màu")
        color_label.setObjectName("deviceFieldName")

        self.selected_color_name = QLabel("--")
        self.selected_color_name.setObjectName("routeSelectedColor")
        self.selected_color_name.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        grid.addWidget(color_label, 0, 0)
        grid.addWidget(
            self.selected_color_name,
            0,
            1,
            1,
            2,
        )

        # --------------------------------------------------------------
        # Row 1: destination
        # --------------------------------------------------------------

        destination_label = QLabel("Vị trí đích")
        destination_label.setObjectName("deviceFieldName")

        self.destination_combo = QComboBox()
        self.destination_combo.setFixedHeight(32)
        self.destination_combo.currentIndexChanged.connect(
            self._on_destination_changed
        )

        grid.addWidget(destination_label, 1, 0)
        grid.addWidget(
            self.destination_combo,
            1,
            1,
            1,
            2,
        )

        # --------------------------------------------------------------
        # Row 2: destination name
        # --------------------------------------------------------------

        name_label = QLabel("Tên vị trí")
        name_label.setObjectName("deviceFieldName")

        self.destination_name = QLineEdit()
        self.destination_name.setPlaceholderText("Ví dụ: BIN A")
        self.destination_name.setFixedHeight(32)

        grid.addWidget(name_label, 2, 0)
        grid.addWidget(
            self.destination_name,
            2,
            1,
            1,
            2,
        )

        # --------------------------------------------------------------
        # Row 3-4: XYZ
        # --------------------------------------------------------------

        xyz_title = QLabel("Tọa độ")
        xyz_title.setObjectName("deviceFieldName")

        grid.addWidget(
            xyz_title,
            3,
            0,
            2,
            1,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )

        self.dest_x = self._detail_float_input()
        self.dest_y = self._detail_float_input()
        self.dest_z = self._detail_float_input()

        xyz_widgets = (
            ("X (mm)", self.dest_x),
            ("Y (mm)", self.dest_y),
            ("Z (mm)", self.dest_z),
        )

        for column, (text, widget) in enumerate(
            xyz_widgets,
            start=1,
        ):
            label = QLabel(text)
            label.setObjectName("deviceFieldName")
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            grid.addWidget(
                label,
                3,
                column,
            )

            grid.addWidget(
                widget,
                4,
                column,
            )

        # --------------------------------------------------------------
        # Row 5: route enabled + usage
        # --------------------------------------------------------------

        self.route_enabled = QCheckBox(
            "Kích hoạt tuyến"
        )
        self.route_enabled.setChecked(True)

        self.destination_usage = QLabel("")
        self.destination_usage.setObjectName("muted")
        self.destination_usage.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        grid.addWidget(
            self.route_enabled,
            5,
            0,
            1,
            2,
        )

        grid.addWidget(
            self.destination_usage,
            5,
            2,
        )

        # --------------------------------------------------------------
        # Row 6: actions
        # --------------------------------------------------------------

        capture_btn = QPushButton(
            "LẤY TỌA ĐỘ PLC"
        )
        capture_btn.setObjectName(
            "secondaryBlueButton"
        )
        capture_btn.setFixedHeight(34)
        capture_btn.clicked.connect(
            self._capture_current_position
        )

        add_destination_btn = QPushButton(
            "THÊM VỊ TRÍ"
        )
        add_destination_btn.setObjectName(
            "secondaryBlueButton"
        )
        add_destination_btn.setFixedHeight(34)
        add_destination_btn.clicked.connect(
            self._add_destination
        )

        grid.addWidget(
            capture_btn,
            6,
            0,
            1,
            2,
        )

        grid.addWidget(
            add_destination_btn,
            6,
            2,
        )

        # --------------------------------------------------------------
        # Row 7: save
        # --------------------------------------------------------------

        save_btn = QPushButton(
            "LƯU TỌA ĐỘ & ROUTING"
        )
        save_btn.setObjectName(
            "positiveButton"
        )
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(
            self._save_selected_route
        )

        grid.addWidget(
            save_btn,
            7,
            0,
            1,
            3,
        )

        # Cột input được ưu tiên không gian.
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        card = SectionCard(
            "CHI TIẾT ĐÃ CHỌN",
            body,
        )

        card.setMinimumHeight(245)

        return card
    # ------------------------------------------------------------------
    # INPUT HELPERS
    # ------------------------------------------------------------------

    def _float_input(
        self,
        *,
        value: float,
        minimum: float,
        maximum: float,
    ) -> QLineEdit:
        edit = QLineEdit(f"{value:.2f}")
        edit.setObjectName("axisInput")
        edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit.setFixedSize(self.AXIS_CELL_WIDTH, self.AXIS_CELL_HEIGHT)
        edit.setValidator(QDoubleValidator(minimum, maximum, 2, edit))
        return edit

    @staticmethod
    def _int_input(value: int, minimum: int, maximum: int) -> QLineEdit:
        edit = QLineEdit(str(value))
        edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit.setValidator(QIntValidator(minimum, maximum, edit))
        edit.setFixedHeight(28)
        return edit

    @staticmethod
    def _detail_float_input() -> QLineEdit:
        edit = QLineEdit("0.00")
        edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit.setFixedHeight(32)
        edit.setValidator(QDoubleValidator(0.0, 99999.0, 2, edit))
        return edit

    @staticmethod
    def _parse_float(edit: QLineEdit, field_name: str) -> float:
        text = edit.text().strip().replace(",", ".")
        if not text:
            raise ValueError(f"{field_name} chưa được nhập.")
        return float(text)

    @staticmethod
    def _parse_int(edit: QLineEdit, field_name: str) -> int:
        text = edit.text().strip()
        if not text:
            raise ValueError(f"{field_name} chưa được nhập.")
        return int(text)

    # ------------------------------------------------------------------
    # AXIS / PLC ACTIONS
    # ------------------------------------------------------------------

    def _request_home(self, axis: str | None) -> None:
        """Chỉ yêu cầu HOME khi PLC cho phép điều khiển tay."""
        status = self.context.plc.get_status()
        if (
            not status.connected
            or status.mode != MachineMode.MANUAL
            or status.fault_code != 0
        ):
            return
        self.context.plc.home_axis(axis)

    def _jog(self, axis: str, direction: float) -> None:
        status = self.context.plc.get_status()
        if (
            not status.connected
            or status.mode != MachineMode.MANUAL
            or status.fault_code != 0
        ):
            return

        controls = self.axis_controls[axis]
        step_mm = self._parse_float(
            controls["jog_step_mm"],
            f"Bước Jog trục {axis.upper()}",
        )
        self.context.plc.jog(axis, direction * step_mm)

    def _save_axis_settings(self) -> None:
        try:
            for axis in self.AXES:
                controls = self.axis_controls[axis]

                max_mm = self._parse_float(
                    controls["max_mm"],
                    f"Max trục {axis.upper()}",
                )
                velocity_mm_s = self._parse_float(
                    controls["velocity_mm_s"],
                    f"Vận tốc trục {axis.upper()}",
                )
                jog_step_mm = self._parse_float(
                    controls["jog_step_mm"],
                    f"Bước Jog trục {axis.upper()}",
                )

                if max_mm <= 0:
                    raise ValueError(
                        f"Max trục {axis.upper()} phải lớn hơn 0."
                    )
                if velocity_mm_s <= 0:
                    raise ValueError(
                        f"Vận tốc trục {axis.upper()} phải lớn hơn 0."
                    )
                if jog_step_mm <= 0:
                    raise ValueError(
                        f"Bước Jog trục {axis.upper()} phải lớn hơn 0."
                    )

                self.context.config.set(
                    f"machine.axes.{axis}.min_mm",
                    0.0,
                    save=False,
                )
                self.context.config.set(
                    f"machine.axes.{axis}.max_mm",
                    max_mm,
                    save=False,
                )
                self.context.config.set(
                    f"machine.axes.{axis}.velocity_mm_s",
                    velocity_mm_s,
                    save=False,
                )
                self.context.config.set(
                    f"machine.axes.{axis}.jog_step_mm",
                    jog_step_mm,
                    save=False,
                )

            self.context.config.save()

        except ValueError as error:
            QMessageBox.warning(self, "Thông số trục", str(error))
            return

        QMessageBox.information(
            self,
            "Thông số trục",
            "Đã lưu Max, vận tốc và bước Jog.\nMin của tất cả trục cố định tại 0 mm.",
        )

    def _save_plc_settings(self) -> None:
        try:
            host = self.plc_host.text().strip()
            if not host:
                raise ValueError("Địa chỉ IP PLC không được để trống.")

            rack = self._parse_int(self.plc_rack, "Rack")
            slot = self._parse_int(self.plc_slot, "Slot")
            command_db = self._parse_int(self.command_db, "Command DB")
            status_db = self._parse_int(self.status_db, "Status DB")

        except ValueError as error:
            QMessageBox.warning(self, "Kết nối PLC", str(error))
            return

        self.context.config.set("plc.host", host, save=False)
        self.context.config.set("plc.rack", rack, save=False)
        self.context.config.set("plc.slot", slot, save=False)
        self.context.config.set("plc.command_db", command_db, save=False)
        self.context.config.set("plc.status_db", status_db, save=False)
        self.context.config.save()

        QMessageBox.information(
            self,
            "Kết nối PLC",
            "Đã lưu cấu hình. Khởi động lại HMI để tạo lại kết nối PLC.",
        )

    # ------------------------------------------------------------------
    # ROUTING DATA
    # ------------------------------------------------------------------

    def _refresh_route_table(self) -> None:
        """Rebuild table và đồng bộ panel chi tiết một cách xác định.

        Chặn signal trong lúc rebuild để tránh selectionChanged chạy giữa chừng,
        đây là nguyên nhân dễ làm bảng hiển thị BIN A nhưng panel phải vẫn ở
        '-- Chưa gán --'.
        """
        colors = self.context.colors.all()

        previous_block_state = self.route_table.blockSignals(True)
        try:
            self.route_table.clearContents()
            self.route_table.setRowCount(len(colors))

            selected_row = -1

            if self.selected_color_id is None and colors:
                self.selected_color_id = colors[0].id

            for row, color in enumerate(colors):
                rule = self.context.routes.get_for_color(color.id)
                destination = None

                if rule is not None:
                    try:
                        destination = self.context.destinations.get(
                            rule.destination_id
                        )
                    except KeyError:
                        destination = None

                color_item = QTableWidgetItem(color.display_name)
                color_item.setData(Qt.ItemDataRole.UserRole, color.id)

                destination_name = (
                    destination.display_name
                    if destination is not None
                    else "Chưa gán"
                )

                values = (
                    color_item,
                    QTableWidgetItem(destination_name),
                    QTableWidgetItem(
                        f"{destination.x:.2f}" if destination else "--"
                    ),
                    QTableWidgetItem(
                        f"{destination.y:.2f}" if destination else "--"
                    ),
                    QTableWidgetItem(
                        f"{destination.z:.2f}" if destination else "--"
                    ),
                    QTableWidgetItem(
                        "ON" if rule is not None and rule.enabled else "OFF"
                    ),
                )

                for column, item in enumerate(values):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.route_table.setItem(row, column, item)

                if color.id == self.selected_color_id:
                    selected_row = row

            if selected_row < 0 and colors:
                selected_row = 0
                self.selected_color_id = colors[0].id

            if selected_row >= 0:
                self.route_table.setCurrentCell(selected_row, 0)
                self.route_table.selectRow(selected_row)

        finally:
            self.route_table.blockSignals(previous_block_state)

        self._apply_route_filter(self.route_search.text())

        # Không phụ thuộc signal sau khi refresh: luôn sync panel phải trực tiếp.
        self._load_selected_color()

    def _apply_route_filter(self, text: str) -> None:
        needle = text.strip().lower()
        visible_count = 0

        for row in range(self.route_table.rowCount()):
            color_item = self.route_table.item(row, 0)
            destination_item = self.route_table.item(row, 1)

            haystack = " ".join(
                (
                    color_item.text() if color_item else "",
                    destination_item.text() if destination_item else "",
                )
            ).lower()

            visible = not needle or needle in haystack
            self.route_table.setRowHidden(row, not visible)

            if visible:
                visible_count += 1

        self.route_count_label.setText(
            f"Hiển thị {visible_count} / {self.route_table.rowCount()} màu"
        )

    def _on_route_current_cell_changed(
        self,
        current_row: int,
        _current_column: int,
        _previous_row: int,
        _previous_column: int,
    ) -> None:
        if current_row < 0:
            return

        item = self.route_table.item(current_row, 0)
        if item is None:
            return

        color_id = item.data(Qt.ItemDataRole.UserRole)
        if color_id is None:
            return

        self.selected_color_id = int(color_id)
        self._load_selected_color()

    def _load_selected_color(self) -> None:
        if self.selected_color_id is None:
            self.selected_color_name.setText("--")
            self._reload_destination_combo(None)
            self.route_enabled.setChecked(False)
            self._load_destination_fields()
            return

        try:
            color = self.context.colors.get(self.selected_color_id)
        except KeyError:
            self.selected_color_name.setText("--")
            return

        rule = self.context.routes.get_for_color(color.id)

        self.selected_color_name.setText(color.display_name)
        self._reload_destination_combo(
            rule.destination_id if rule is not None else None
        )
        self.route_enabled.setChecked(
            rule.enabled if rule is not None else True
        )
        self._load_destination_fields()

    def _reload_destination_combo(
        self,
        selected_destination_id: int | None,
    ) -> None:
        old_state = self.destination_combo.blockSignals(True)
        try:
            self.destination_combo.clear()
            self.destination_combo.addItem("-- Chưa gán --", None)

            for destination in self.context.destinations.all():
                suffix = "" if destination.enabled else " [OFF]"
                self.destination_combo.addItem(
                    f"{destination.display_name}{suffix}",
                    destination.id,
                )

            index = 0
            if selected_destination_id is not None:
                found = self.destination_combo.findData(
                    int(selected_destination_id)
                )
                if found >= 0:
                    index = found

            self.destination_combo.setCurrentIndex(index)

        finally:
            self.destination_combo.blockSignals(old_state)

    def _on_destination_changed(self, _index: int) -> None:
        self._load_destination_fields()

    def _load_destination_fields(self) -> None:
        destination_id = self.destination_combo.currentData()
        has_destination = destination_id is not None

        for widget in (
            self.destination_name,
            self.dest_x,
            self.dest_y,
            self.dest_z,
        ):
            widget.setEnabled(has_destination)

        if not has_destination:
            self.destination_name.clear()
            self.dest_x.setText("0.00")
            self.dest_y.setText("0.00")
            self.dest_z.setText("0.00")
            self.destination_usage.setText("Chưa gán vị trí")
            return

        try:
            destination = self.context.destinations.get(int(destination_id))
        except KeyError:
            self.destination_usage.setText("Destination không tồn tại")
            return

        self.destination_name.setText(destination.display_name)
        self.dest_x.setText(f"{destination.x:.2f}")
        self.dest_y.setText(f"{destination.y:.2f}")
        self.dest_z.setText(f"{destination.z:.2f}")

        users = self.context.routing_service.colors_for_destination(
            destination.id
        )
        self.destination_usage.setText(
            f"{len(users)} màu dùng vị trí này"
        )

    def _capture_current_position(self) -> None:
        if self.destination_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Vị trí",
                "Chọn hoặc thêm một Destination trước.",
            )
            return

        status = self.context.plc.get_status()
        if not status.connected:
            QMessageBox.warning(
                self,
                "Vị trí",
                "PLC đang mất kết nối nên chưa thể lấy tọa độ.",
            )
            return

        self.dest_x.setText(f"{status.axes.x:.2f}")
        self.dest_y.setText(f"{status.axes.y:.2f}")
        self.dest_z.setText(f"{status.axes.z:.2f}")

    def _save_selected_route(self) -> None:
        if self.selected_color_id is None:
            QMessageBox.warning(
                self,
                "Routing",
                "Chọn một màu trong bảng trước.",
            )
            return

        destination_id = self.destination_combo.currentData()

        if destination_id is None:
            self.context.routes.remove_route(self.selected_color_id)
            self._refresh_route_table()
            QMessageBox.information(
                self,
                "Routing",
                "Đã bỏ gán vị trí của màu đang chọn.",
            )
            return

        try:
            current = self.context.destinations.get(int(destination_id))

            name = self.destination_name.text().strip()
            if not name:
                raise ValueError("Tên vị trí không được để trống.")

            x = self._parse_float(self.dest_x, "X")
            y = self._parse_float(self.dest_y, "Y")
            z = self._parse_float(self.dest_z, "Z")

            self._validate_destination_coordinates(x, y, z)

            updated = Destination(
                id=current.id,
                key=current.key,
                display_name=name,
                x=x,
                y=y,
                z=z,
                enabled=current.enabled,
            )

            self.context.destinations.update(updated)
            self.context.routes.set_route(
                self.selected_color_id,
                updated.id,
                enabled=self.route_enabled.isChecked(),
            )

        except (KeyError, ValueError) as error:
            QMessageBox.warning(self, "Routing", str(error))
            return

        self._refresh_route_table()

        QMessageBox.information(
            self,
            "Routing",
            "Đã lưu tọa độ Destination và quy tắc Color → Destination.",
        )

    def _add_destination(self) -> None:
        used_ids = {
            item.id
            for item in self.context.destinations.all()
        }

        next_id = 1
        while next_id in used_ids:
            next_id += 1

        status = self.context.plc.get_status()

        x = status.axes.x if status.connected else 0.0
        y = status.axes.y if status.connected else 0.0
        z = status.axes.z if status.connected else 0.0

        destination = Destination(
            id=next_id,
            key=f"position_{next_id}",
            display_name=f"VỊ TRÍ {next_id}",
            x=x,
            y=y,
            z=z,
            enabled=True,
        )

        try:
            self.context.destinations.add(destination)
        except ValueError as error:
            QMessageBox.warning(self, "Vị trí", str(error))
            return

        # Chọn destination mới cho màu hiện tại nhưng chưa lưu route cho tới
        # khi người dùng bấm LƯU TỌA ĐỘ & ROUTING.
        self._reload_destination_combo(destination.id)
        self._load_destination_fields()

        QMessageBox.information(
            self,
            "Vị trí",
            (
                f"Đã tạo {destination.display_name}.\n"
                "Đổi tên/XYZ rồi bấm LƯU TỌA ĐỘ & ROUTING."
            ),
        )

    def _validate_destination_coordinates(
        self,
        x: float,
        y: float,
        z: float,
    ) -> None:
        for axis, value in {"x": x, "y": y, "z": z}.items():
            max_mm = float(
                self.context.config.get(
                    f"machine.axes.{axis}.max_mm",
                    9999.0,
                )
            )

            if value < 0.0 or value > max_mm:
                raise ValueError(
                    f"Tọa độ {axis.upper()}={value:.2f} mm nằm ngoài "
                    f"vùng 0..{max_mm:.2f} mm."
                )

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        self._refresh_axes(status)
        self._refresh_outputs(status)
        self._refresh_plc(status)

    def _refresh_axes(self, status: PLCStatus) -> None:
        positions = {
            "x": status.axes.x,
            "y": status.axes.y,
            "z": status.axes.z,
        }

        # Không được cho JOG/HOME khi PLC ở AUTO hay đang có fault.
        axis_enabled = (
            status.connected
            and status.mode == MachineMode.MANUAL
            and status.fault_code == 0
        )

        for axis in self.AXES:
            controls = self.axis_controls[axis]
            controls["position_mm"].setText(f"{positions[axis]:.2f}")
            controls["jog_minus"].setEnabled(axis_enabled)
            controls["jog_plus"].setEnabled(axis_enabled)
            controls["home"].setEnabled(axis_enabled)

        self.home_all_btn.setEnabled(axis_enabled)

    def _refresh_outputs(self, status: PLCStatus) -> None:
        self.vacuum_led.set_text(
            "Đang bật" if status.vacuum_on else "Đang tắt"
        )
        self.vacuum_led.set_active(status.vacuum_on)

        self.conveyor_led.set_text(
            "Đang chạy" if status.conveyor_on else "Đang dừng"
        )
        self.conveyor_led.set_active(status.conveyor_on)

        manual_enabled = (
            status.connected
            and status.mode == MachineMode.MANUAL
            and status.fault_code == 0
        )

        for button in (
            *self.vacuum_buttons,
            *self.conveyor_buttons,
        ):
            button.setEnabled(manual_enabled)

    def _refresh_plc(self, status: PLCStatus) -> None:
        if status.connected:
            self.plc_led.set_text("Đã kết nối")
            self.plc_led.set_active(True)
        else:
            self.plc_led.set_text("Mất kết nối")
            self.plc_led.set_active(False, fault=True)
