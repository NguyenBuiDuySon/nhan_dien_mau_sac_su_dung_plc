from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from domain.destination import Destination
from ui.pages.base_page import BasePage
from ui.widgets import SectionCard, StatusLed


class SettingsPage(BasePage):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__(
            "MÀN HÌNH CÀI ĐẶT",
            "Cấu hình kết nối, vị trí phân loại và các tham số vận hành",
            "⚙",
        )
        self.context = context

        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(self._build_plc_card(), 3)
        top.addWidget(self._build_camera_card(), 3)
        self.root.addLayout(top)

        middle = QHBoxLayout()
        middle.setSpacing(10)
        middle.addWidget(self._build_destination_card(), 3)
        middle.addWidget(self._build_routing_card(), 2)
        self.root.addLayout(middle, 1)

        footer = QHBoxLayout()
        note = QLabel("Tọa độ HMI dùng mm. PLC/Technology Object chịu trách nhiệm đổi mm sang pulse theo cơ khí.")
        note.setObjectName("muted")
        footer.addWidget(note, 1)
        save_all = QPushButton("LƯU CẤU HÌNH")
        save_all.setObjectName("secondaryBlueButton")
        save_all.clicked.connect(self._save_connection_settings)
        footer.addWidget(save_all)
        self.root.addLayout(footer)
        self._refresh_destinations()
        self._refresh_routes()
        self.refresh()

    def _build_plc_card(self) -> SectionCard:
        body = QWidget()
        form = QFormLayout(body)
        self.plc_driver = QComboBox()
        self.plc_driver.addItems(["mock", "s7"])
        self.plc_driver.setCurrentText(str(self.context.config.get("plc.driver", "mock")))
        self.plc_host = QLineEdit(str(self.context.config.get("plc.host", "192.168.0.10")))
        self.plc_rack = QSpinBox(); self.plc_rack.setRange(0, 7); self.plc_rack.setValue(int(self.context.config.get("plc.rack", 0)))
        self.plc_slot = QSpinBox(); self.plc_slot.setRange(0, 31); self.plc_slot.setValue(int(self.context.config.get("plc.slot", 1)))
        self.plc_command_db = QSpinBox(); self.plc_command_db.setRange(1, 65535); self.plc_command_db.setValue(int(self.context.config.get("plc.command_db", 100)))
        self.plc_status_db = QSpinBox(); self.plc_status_db.setRange(1, 65535); self.plc_status_db.setValue(int(self.context.config.get("plc.status_db", 101)))
        self.plc_led = StatusLed("Đang kiểm tra")
        for label, widget in (
            ("Driver", self.plc_driver), ("Địa chỉ IP", self.plc_host), ("Rack", self.plc_rack),
            ("Slot", self.plc_slot), ("Command DB", self.plc_command_db), ("Status DB", self.plc_status_db),
            ("Trạng thái", self.plc_led),
        ):
            form.addRow(label, widget)
        note = QLabel("Đổi driver/IP cần khởi động lại HMI để tạo PLCService mới.")
        note.setWordWrap(True); note.setObjectName("muted")
        form.addRow(note)
        return SectionCard("CÀI ĐẶT KẾT NỐI PLC", body, title_icon="▥")

    def _build_camera_card(self) -> SectionCard:
        body = QWidget()
        form = QFormLayout(body)
        self.camera_source = QSpinBox(); self.camera_source.setRange(0, 16); self.camera_source.setValue(int(self.context.config.get("camera.source", 0)))
        self.camera_width = QSpinBox(); self.camera_width.setRange(320, 3840); self.camera_width.setValue(int(self.context.config.get("camera.width", 1280)))
        self.camera_height = QSpinBox(); self.camera_height.setRange(240, 2160); self.camera_height.setValue(int(self.context.config.get("camera.height", 720)))
        self.camera_fps = QSpinBox(); self.camera_fps.setRange(1, 120); self.camera_fps.setValue(int(self.context.config.get("camera.fps", 30)))
        self.camera_led = StatusLed("Offline")
        for label, widget in (
            ("Nguồn camera", self.camera_source), ("Chiều rộng", self.camera_width),
            ("Chiều cao", self.camera_height), ("FPS", self.camera_fps), ("Trạng thái", self.camera_led),
        ):
            form.addRow(label, widget)
        return SectionCard("CÀI ĐẶT CAMERA", body, title_icon="▣")

    def _build_destination_card(self) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        self.destination_table = QTableWidget(0, 6)
        self.destination_table.setHorizontalHeaderLabels(["ID", "Tên", "X (mm)", "Y (mm)", "Z (mm)", "Bật"])
        self.destination_table.setAlternatingRowColors(True)
        layout.addWidget(self.destination_table, 1)
        save = QPushButton("LƯU TỌA ĐỘ")
        save.setObjectName("secondaryBlueButton")
        save.clicked.connect(self._save_destinations)
        layout.addWidget(save)
        return SectionCard("ĐIỂM MÁY / VỊ TRÍ PHÂN LOẠI", body, title_icon="⌖")

    def _build_routing_card(self) -> SectionCard:
        body = QWidget()
        layout = QVBoxLayout(body)
        self.route_table = QTableWidget(0, 2)
        self.route_table.setHorizontalHeaderLabels(["Màu", "Vị trí đích"])
        self.route_table.setAlternatingRowColors(True)
        layout.addWidget(self.route_table, 1)
        save = QPushButton("LƯU ROUTING")
        save.setObjectName("secondaryBlueButton")
        save.clicked.connect(self._save_routing)
        layout.addWidget(save)
        return SectionCard("QUY TẮC PHÂN LOẠI", body, title_icon="⇢")

    def refresh(self) -> None:
        status = self.context.plc.get_status()
        self.plc_led.set_text("Đã kết nối" if status.connected else "Chưa kết nối")
        self.plc_led.set_active(status.connected, fault=not status.connected and self.plc_driver.currentText() == "s7")
        self.camera_led.set_text("Online" if self.context.camera.running else "Offline")
        self.camera_led.set_active(self.context.camera.running)

    def _refresh_destinations(self) -> None:
        destinations = self.context.destinations.all()
        self.destination_table.setRowCount(len(destinations))
        for row, destination in enumerate(destinations):
            values = [destination.id, destination.display_name, destination.x, destination.y, destination.z, "YES" if destination.enabled else "NO"]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column in (0, 1):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.destination_table.setItem(row, column, item)

    def _refresh_routes(self) -> None:
        colors = self.context.colors.all()
        destinations = self.context.destinations.enabled()
        self.route_table.setRowCount(len(colors))
        for row, color in enumerate(colors):
            name_item = QTableWidgetItem(color.display_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.route_table.setItem(row, 0, name_item)
            combo = QComboBox()
            for destination in destinations:
                combo.addItem(destination.display_name, destination.id)
            rule = self.context.routes.get_for_color(color.id)
            if rule is not None:
                index = combo.findData(rule.destination_id)
                if index >= 0:
                    combo.setCurrentIndex(index)
            combo.setProperty("colorId", color.id)
            self.route_table.setCellWidget(row, 1, combo)

    def _save_connection_settings(self) -> None:
        self.context.config.set("plc.driver", self.plc_driver.currentText(), save=False)
        self.context.config.set("plc.host", self.plc_host.text().strip(), save=False)
        self.context.config.set("plc.rack", self.plc_rack.value(), save=False)
        self.context.config.set("plc.slot", self.plc_slot.value(), save=False)
        self.context.config.set("plc.command_db", self.plc_command_db.value(), save=False)
        self.context.config.set("plc.status_db", self.plc_status_db.value(), save=False)
        self.context.config.set("camera.source", self.camera_source.value(), save=False)
        self.context.config.set("camera.width", self.camera_width.value(), save=False)
        self.context.config.set("camera.height", self.camera_height.value(), save=False)
        self.context.config.set("camera.fps", self.camera_fps.value(), save=False)
        self.context.config.save()
        QMessageBox.information(self, "Cấu hình", "Đã lưu cấu hình. Đổi driver/IP PLC có hiệu lực sau khi mở lại HMI.")

    def _save_destinations(self) -> None:
        try:
            for row in range(self.destination_table.rowCount()):
                destination_id = int(self.destination_table.item(row, 0).text())
                current = self.context.destinations.get(destination_id)
                updated = Destination(
                    id=current.id,
                    key=current.key,
                    display_name=current.display_name,
                    x=float(self.destination_table.item(row, 2).text()),
                    y=float(self.destination_table.item(row, 3).text()),
                    z=float(self.destination_table.item(row, 4).text()),
                    enabled=self.destination_table.item(row, 5).text().strip().upper() not in {"NO", "0", "FALSE"},
                )
                self.context.destinations.update(updated)
        except Exception as error:
            QMessageBox.warning(self, "Tọa độ", str(error))
            return
        QMessageBox.information(self, "Tọa độ", "Đã lưu các vị trí phân loại theo đơn vị mm.")
        self._refresh_destinations()

    def _save_routing(self) -> None:
        try:
            for row in range(self.route_table.rowCount()):
                combo = self.route_table.cellWidget(row, 1)
                if not isinstance(combo, QComboBox):
                    continue
                color_id = int(combo.property("colorId"))
                destination_id = int(combo.currentData())
                self.context.routes.set_route(color_id, destination_id, enabled=True)
        except Exception as error:
            QMessageBox.warning(self, "Routing", str(error))
            return
        QMessageBox.information(self, "Routing", "Đã lưu quy tắc Color → Destination.")
