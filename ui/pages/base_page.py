from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

class BasePage(QWidget):
    """Khung tiêu đề dùng chung cho các màn hình HMI."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: str = "",  # Giữ tham số để code cũ chưa cần sửa đồng loạt.
    ) -> None:
        super().__init__()

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 16, 18, 18)
        self.root.setSpacing(12)

        header = QFrame()
        header.setObjectName("pageHeader")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 10, 22, 10)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        layout.addStretch()

        if subtitle:
            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.VLine)
            divider.setObjectName("headerDivider")

            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("pageSubtitle")
            subtitle_label.setWordWrap(False)
            subtitle_label.setMinimumWidth(430)
            subtitle_label.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            layout.addWidget(divider)
            layout.addWidget(subtitle_label)

        self.root.addWidget(header)