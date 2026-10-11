from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StatusLed(QWidget):
    """Đèn trạng thái HMI nhỏ, dùng chung cho PLC/Camera/Interlock."""

    def __init__(self, text: str = "", active: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        self.dot = QLabel()
        self.dot.setFixedSize(18, 18)
        self.label = QLabel(text)
        self.label.setObjectName("statusText")
        layout.addWidget(self.dot)
        layout.addWidget(self.label, 1)
        self.set_active(active)

    def set_active(self, active: bool, *, warning: bool = False, fault: bool = False) -> None:
        if fault:
            color = "#ef4444"
            glow = "#7f1d1d"
        elif warning:
            color = "#facc15"
            glow = "#713f12"
        elif active:
            color = "#22c55e"
            glow = "#14532d"
        else:
            color = "#64748b"
            glow = "#334155"
        self.dot.setStyleSheet(
            f"background:{color}; border:3px solid {glow}; border-radius:9px;"
        )

    def set_text(self, text: str) -> None:
        self.label.setText(text)


class SectionCard(QFrame):
    """Panel công nghiệp với header riêng, giống card trong mockup."""

    def __init__(
        self,
        title: str,
        body: QWidget | None = None,
        *,
        title_icon: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        if title_icon:
            icon = QLabel(title_icon)
            icon.setObjectName("sectionIcon")
            header.addWidget(icon)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        header.addWidget(title_label)
        header.addStretch()
        root.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sectionLine")
        root.addWidget(line)

        self.body_layout = QVBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(8)
        if body is not None:
            self.body_layout.addWidget(body)
        root.addLayout(self.body_layout, 1)


class MetricValue(QFrame):
    """Ô giá trị lớn cho vị trí trục và các metric quan trọng."""

    def __init__(self, label: str, value: str = "-", unit: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        caption = QLabel(label)
        caption.setObjectName("metricCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout()
        row.setSpacing(5)
        row.addStretch()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.value_label)
        if unit:
            unit_label = QLabel(unit)
            unit_label.setObjectName("metricUnit")
            row.addWidget(unit_label)
        row.addStretch()

        layout.addWidget(caption)
        layout.addLayout(row)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class CounterRow(QWidget):
    def __init__(self, name: str, color: str, count: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        swatch = QLabel()
        swatch.setFixedSize(30, 30)
        swatch.setStyleSheet(f"background:{color}; border-radius:5px; border:1px solid #64748b;")
        name_label = QLabel(name)
        name_label.setObjectName("counterName")
        self.count_label = QLabel(f"{count:04d}")
        self.count_label.setObjectName("counterValue")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(swatch)
        layout.addWidget(name_label, 1)
        layout.addWidget(self.count_label)

    def set_count(self, value: int) -> None:
        self.count_label.setText(f"{max(0, int(value)):04d}")
