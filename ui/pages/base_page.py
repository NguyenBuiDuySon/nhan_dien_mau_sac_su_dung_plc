from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class BasePage(QWidget):
    """Base page dùng chung header công nghiệp cho mọi screen."""

    def __init__(self, title: str, subtitle: str = "", icon: str = "◉") -> None:
        super().__init__()
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 16, 18, 18)
        self.root.setSpacing(12)

        header = QFrame()
        header.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 10, 18, 10)
        header_layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setObjectName("pageIcon")
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        if subtitle:
            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.VLine)
            divider.setStyleSheet("color:#43576b;")
            header_layout.addWidget(divider)
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("pageSubtitle")
            subtitle_label.setWordWrap(True)
            header_layout.addWidget(subtitle_label)

        self.root.addWidget(header)
