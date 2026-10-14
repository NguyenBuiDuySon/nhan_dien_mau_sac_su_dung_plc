"""Hộp thoại thêm/sửa/xóa màu. Dải HSV được chỉnh trên trang Vision."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.context import ApplicationContext
from domain.machine import MachineState
from services.color_management_service import ColorManagementService


class ColorManagerDialog(QDialog):
    """Quản lý thông tin màu và trạng thái kích hoạt; không sửa Routing."""

    # -1 nghĩa là màu đang chọn đã bị xóa.
    colors_modified = Signal(int)

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.context = context
        self.manager = ColorManagementService(context.colors, context.routes, context.state)
        self._ui_color = "#38bdf8"
        self.setWindowTitle("Quản lý màu - Vision")
        self.setMinimumSize(620, 420)

        outer = QVBoxLayout(self)
        note = QLabel("Chỉnh HSV ở màn hình Vision. Routing và tọa độ được quản lý tại Manual.")
        note.setWordWrap(True)
        outer.addWidget(note)

        content = QHBoxLayout()
        self.color_list = QListWidget()
        self.color_list.setMinimumWidth(220)
        self.color_list.currentItemChanged.connect(self._load_selected)
        content.addWidget(self.color_list, 2)

        details = QWidget()
        right = QVBoxLayout(details)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(60)
        form.addRow("Tên màu:", self.name_edit)
        self.id_value = QLabel("--")
        form.addRow("Color ID:", self.id_value)
        self.key_value = QLabel("--")
        form.addRow("Key (cố định):", self.key_value)
        self.pick_color_btn = QPushButton("Chọn màu hiển thị")
        self.pick_color_btn.clicked.connect(self._choose_ui_color)
        form.addRow("Màu giao diện:", self.pick_color_btn)
        self.enabled_check = QCheckBox("Cho phép nhận diện màu này")
        form.addRow("Kích hoạt:", self.enabled_check)
        right.addLayout(form)

        hint = QLabel("Màu mới mặc định tắt. Cần chỉnh HSV rồi mới bật nhận diện.")
        hint.setWordWrap(True)
        right.addWidget(hint)
        right.addStretch(1)

        save = QPushButton("LƯU THÔNG TIN MÀU")
        save.setObjectName("secondaryBlueButton")
        save.clicked.connect(self._save_selected)
        right.addWidget(save)
        content.addWidget(details, 3)
        outer.addLayout(content, 1)

        actions = QHBoxLayout()
        add = QPushButton("THÊM MÀU")
        add.setObjectName("positiveButton")
        add.clicked.connect(self._add_color)
        delete = QPushButton("XÓA MÀU")
        delete.setObjectName("negativeButton")
        delete.clicked.connect(self._delete_selected)
        close = QPushButton("ĐÓNG")
        close.clicked.connect(self.accept)
        actions.addWidget(add)
        actions.addWidget(delete)
        actions.addStretch(1)
        actions.addWidget(close)
        outer.addLayout(actions)

        self._reload_list()

    def _selected_id(self) -> int | None:
        item = self.color_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def _reload_list(self, preferred_id: int | None = None) -> None:
        previous_id = preferred_id if preferred_id is not None else self._selected_id()
        old_signals = self.color_list.blockSignals(True)
        try:
            self.color_list.clear()
            for profile in self.context.colors.all():
                state = "" if profile.enabled else " [TẮT]"
                item = QListWidgetItem(f"{profile.id:02d}  {profile.display_name}{state}")
                item.setData(Qt.ItemDataRole.UserRole, profile.id)
                self.color_list.addItem(item)
            row = 0
            for index in range(self.color_list.count()):
                item = self.color_list.item(index)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) == previous_id:
                    row = index
                    break
            if self.color_list.count() > 0:
                self.color_list.setCurrentRow(row)
        finally:
            self.color_list.blockSignals(old_signals)
        self._load_selected()

    def _load_selected(self, *_args: object) -> None:
        color_id = self._selected_id()
        has_color = color_id is not None
        for widget in (self.name_edit, self.pick_color_btn, self.enabled_check):
            widget.setEnabled(has_color)
        if color_id is None:
            self.name_edit.clear()
            self.id_value.setText("--")
            self.key_value.setText("--")
            self.enabled_check.setChecked(False)
            return
        profile = self.context.colors.get(color_id)
        self.name_edit.setText(profile.display_name)
        self.id_value.setText(str(profile.id))
        self.key_value.setText(profile.key)
        self.enabled_check.setChecked(profile.enabled)
        self._ui_color = profile.ui_color
        self.pick_color_btn.setText(f"Màu: {profile.ui_color}")

    def _editing_allowed(self) -> bool:
        if self.context.plc.get_status().state == MachineState.RUNNING:
            QMessageBox.warning(self, "Đang chạy AUTO", "Dừng chu trình AUTO trước khi sửa cấu hình màu.")
            return False
        return True

    def _choose_ui_color(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._ui_color), self, "Chọn màu hiển thị")
        if chosen.isValid():
            self._ui_color = chosen.name()
            self.pick_color_btn.setText(f"Màu: {self._ui_color}")

    def _add_color(self) -> None:
        if not self._editing_allowed():
            return
        name, accepted = QInputDialog.getText(self, "Thêm màu", "Tên màu mới:")
        if not accepted or not name.strip():
            return
        try:
            profile = self.manager.create(name, "#94a3b8")
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Không thêm được màu", str(error))
            return
        self._reload_list(profile.id)
        self.colors_modified.emit(profile.id)
        QMessageBox.information(
            self, "Màu mới", "Đã thêm màu ở trạng thái TẮT. Đóng hộp thoại để chỉnh HSV tại Vision."
        )

    def _save_selected(self) -> None:
        if not self._editing_allowed():
            return
        color_id = self._selected_id()
        if color_id is None:
            return
        try:
            self.manager.update(
                color_id,
                self.name_edit.text(),
                self._ui_color,
                self.enabled_check.isChecked(),
            )
        except (ValueError, OSError, KeyError) as error:
            QMessageBox.warning(self, "Không lưu được màu", str(error))
            return
        self._reload_list(color_id)
        self.colors_modified.emit(color_id)

    def _delete_selected(self) -> None:
        if not self._editing_allowed():
            return
        color_id = self._selected_id()
        if color_id is None:
            return
        profile = self.context.colors.get(color_id)
        answer = QMessageBox.question(
            self,
            "Xác nhận xóa màu",
            f"Xóa vĩnh viễn '{profile.display_name}' (ID {profile.id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.delete(color_id)
        except (KeyError, ValueError, OSError) as error:
            QMessageBox.warning(self, "Không xóa được màu", str(error))
            return
        self._reload_list()
        self.colors_modified.emit(-1)
