from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.context import ApplicationContext
from ui.main_window import MainWindow
from ui.theme import APP_STYLE


def main() -> int:
    """Điểm vào duy nhất của ứng dụng HMI V04."""
    app = QApplication(sys.argv)
    app.setApplicationName("Color Sorting HMI V04 PLC")
    app.setStyleSheet(APP_STYLE)

    context = ApplicationContext.create_default()
    window = MainWindow(context)
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
