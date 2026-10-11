from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from ui.pages.base_page import BasePage
from ui.widgets import CameraView, SectionCard, StatusLed


class VisionPage(BasePage):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH VISION",
            "Camera, ROI và cấu hình HSV được xử lý phía PC; PLC chỉ nhận kết quả phân loại",
            "◉",
        )
        self.context = context
        self._loading_hsv = False

        content = QHBoxLayout()
        content.setSpacing(10)
        left = QVBoxLayout()
        self.camera_view = CameraView("CAMERA OFFLINE")
        self.context.camera.frame_ready.connect(self.camera_view.set_frame)
        left.addWidget(SectionCard("HÌNH ẢNH CAMERA TRỰC TIẾP", self.camera_view, title_icon="▣"), 1)
        left.addWidget(self._build_camera_controls())
        content.addLayout(left, 5)

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(self._build_result_card(), 2)
        right.addWidget(self._build_hsv_card(), 4)
        right.addWidget(self._build_color_legend(), 2)
        content.addLayout(right, 3)
        self.root.addLayout(content, 1)
        self._reload_colors()
        self.refresh()

    def _build_camera_controls(self) -> SectionCard:
        body = QWidget()
        layout = QHBoxLayout(body)
        self.camera_button = QPushButton("▣  Bật camera")
        self.camera_button.setObjectName("cameraOnButton")
        self.camera_button.clicked.connect(self._toggle_camera)
        background = QPushButton("▧  Lấy nền")
        background.setObjectName("secondaryBlueButton")
        background.setEnabled(False)
        background.setToolTip("Sẽ port background subtraction V03 ở Stage Vision tiếp theo")
        calibrate = QPushButton("☷  Hiệu chỉnh màu")
        calibrate.setObjectName("secondaryYellowButton")
        calibrate.clicked.connect(lambda: self.color_combo.setFocus())
        roi = QPushButton("⌗  Lưu ROI")
        roi.setObjectName("secondaryRedButton")
        roi.setEnabled(False)
        roi.setToolTip("ROI kéo-thả sẽ port từ roi_camera_label.py V03")
        for button in (self.camera_button, background, calibrate, roi):
            layout.addWidget(button)
        return SectionCard("ĐIỀU KHIỂN CAMERA & XỬ LÝ ẢNH", body, title_icon="▣")

    def _build_result_card(self) -> SectionCard:
        body = QWidget()
        grid = QGridLayout(body)
        grid.addWidget(QLabel("Màu sắc nhận diện"), 0, 0)
        self.detected_color = QLabel("--")
        self.detected_color.setObjectName("metricValue")
        grid.addWidget(self.detected_color, 0, 1)
        grid.addWidget(QLabel("Độ tin cậy"), 1, 0)
        self.confidence = QLabel("-- %")
        self.confidence.setObjectName("metricValue")
        grid.addWidget(self.confidence, 1, 1)
        grid.addWidget(QLabel("Trạng thái"), 2, 0)
        self.result_led = StatusLed("Chưa có kết quả")
        grid.addWidget(self.result_led, 2, 1)
        return SectionCard("KẾT QUẢ NHẬN DIỆN", body, title_icon="▥")

    def _build_hsv_card(self) -> SectionCard:
        body = QWidget()
        root = QVBoxLayout(body)
        selector = QHBoxLayout()
        selector.addWidget(QLabel("Màu:"))
        self.color_combo = QComboBox()
        self.color_combo.currentIndexChanged.connect(self._load_color)
        selector.addWidget(self.color_combo, 1)
        selector.addWidget(QLabel("Dải:"))
        self.range_combo = QComboBox()
        self.range_combo.currentIndexChanged.connect(self._load_range)
        selector.addWidget(self.range_combo)
        root.addLayout(selector)

        grid = QGridLayout()
        self.hsv_inputs: dict[str, QSpinBox] = {}
        specs = [
            ("low_h", "Low H", 0, 179), ("high_h", "High H", 0, 179),
            ("low_s", "Low S", 0, 255), ("high_s", "High S", 0, 255),
            ("low_v", "Low V", 0, 255), ("high_v", "High V", 0, 255),
        ]
        for index, (key, label, minimum, maximum) in enumerate(specs):
            spin = QSpinBox()
            spin.setRange(minimum, maximum)
            self.hsv_inputs[key] = spin
            grid.addWidget(QLabel(label), index // 2, (index % 2) * 2)
            grid.addWidget(spin, index // 2, (index % 2) * 2 + 1)
        root.addLayout(grid)

        save = QPushButton("LƯU DẢI HSV HIỆN TẠI")
        save.setObjectName("secondaryBlueButton")
        save.clicked.connect(self._save_hsv)
        root.addWidget(save)
        note = QLabel("H của OpenCV dùng 0..179; S/V dùng 0..255. Một màu có thể có nhiều dải HSV.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        root.addWidget(note)
        return SectionCard("NGƯỠNG MÀU HSV", body, title_icon="⚙")

    def _build_color_legend(self) -> SectionCard:
        self.legend_body = QWidget()
        self.legend_layout = QHBoxLayout(self.legend_body)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        return SectionCard("MÀU SẢN PHẨM (THAM KHẢO)", self.legend_body, title_icon="●")

    def _reload_colors(self) -> None:
        self.color_combo.blockSignals(True)
        self.color_combo.clear()
        for color in self.context.colors.all():
            self.color_combo.addItem(color.display_name, color.id)
        self.color_combo.blockSignals(False)
        self._rebuild_legend()
        if self.color_combo.count():
            self.color_combo.setCurrentIndex(0)
            self._load_color()

    def _rebuild_legend(self) -> None:
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for color in self.context.colors.enabled():
            label = QLabel(f"■  {color.display_name}")
            label.setStyleSheet(f"color:{color.ui_color}; font-weight:700;")
            self.legend_layout.addWidget(label)
        self.legend_layout.addStretch()

    def _load_color(self) -> None:
        color_id = self.color_combo.currentData()
        if color_id is None:
            return
        profile = self.context.colors.get(int(color_id))
        self.range_combo.blockSignals(True)
        self.range_combo.clear()
        for index, _ in enumerate(profile.hsv_ranges):
            self.range_combo.addItem(f"Dải {index + 1}", index)
        self.range_combo.blockSignals(False)
        if self.range_combo.count():
            self.range_combo.setCurrentIndex(0)
            self._load_range()

    def _load_range(self) -> None:
        color_id = self.color_combo.currentData()
        range_index = self.range_combo.currentData()
        if color_id is None or range_index is None:
            return
        profile = self.context.colors.get(int(color_id))
        hsv = profile.hsv_ranges[int(range_index)]
        self._loading_hsv = True
        values = {
            "low_h": hsv.lower[0], "low_s": hsv.lower[1], "low_v": hsv.lower[2],
            "high_h": hsv.upper[0], "high_s": hsv.upper[1], "high_v": hsv.upper[2],
        }
        for key, value in values.items():
            self.hsv_inputs[key].setValue(value)
        self._loading_hsv = False

    def _save_hsv(self) -> None:
        color_id = self.color_combo.currentData()
        range_index = self.range_combo.currentData()
        if color_id is None or range_index is None:
            return
        profile = deepcopy(self.context.colors.get(int(color_id)))
        from domain.color_profile import HSVRange

        new_range = HSVRange(
            lower=(self.hsv_inputs["low_h"].value(), self.hsv_inputs["low_s"].value(), self.hsv_inputs["low_v"].value()),
            upper=(self.hsv_inputs["high_h"].value(), self.hsv_inputs["high_s"].value(), self.hsv_inputs["high_v"].value()),
        )
        new_range.validate()
        profile.hsv_ranges[int(range_index)] = new_range
        try:
            self.context.colors.update(profile)
        except Exception as error:
            QMessageBox.warning(self, "Không lưu được HSV", str(error))
            return
        QMessageBox.information(self, "HSV", "Đã lưu dải HSV hiện tại.")

    def _toggle_camera(self) -> None:
        if self.context.camera.running:
            self.context.camera.stop()
            return
        source = self.context.config.get("camera.source", 0)
        self.context.camera.start(
            source,
            int(self.context.config.get("camera.width", 1280)),
            int(self.context.config.get("camera.height", 720)),
            int(self.context.config.get("camera.fps", 30)),
        )

    def refresh(self) -> None:
        running = self.context.camera.running
        self.camera_button.setText("■  Tắt camera" if running else "▣  Bật camera")
        if not running and self.context.camera.last_error:
            self.camera_view.clear_frame(self.context.camera.last_error)

        result = self.context.state.current_detection
        if result is None:
            self.detected_color.setText("--")
            self.confidence.setText("-- %")
            self.result_led.set_text("Chưa có kết quả")
            self.result_led.set_active(False)
            return

        if result.color_id is None:
            self.detected_color.setText("Không xác định")
            self.confidence.setText(f"{result.confidence * 100:.0f} %")
            self.result_led.set_text("Không hợp lệ")
            self.result_led.set_active(False, warning=True)
            return

        color = self.context.colors.get(result.color_id)
        self.detected_color.setText(color.display_name)
        self.confidence.setText(f"{result.confidence * 100:.0f} %")
        self.result_led.set_text("Ổn định" if result.stable else "Đang xác nhận")
        self.result_led.set_active(result.stable, warning=not result.stable)
