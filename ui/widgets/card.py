from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


def make_card(title: str, body: QWidget | None = None) -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    layout = QVBoxLayout(card)
    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: 800; font-size: 14px;")
    layout.addWidget(title_label)
    if body is not None:
        layout.addWidget(body, 1)
    return card
