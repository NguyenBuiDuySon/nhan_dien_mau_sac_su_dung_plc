from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel


class CameraView(QLabel):
    """Widget hiển thị frame OpenCV mà không tự sở hữu camera."""

    def __init__(self, placeholder: str = "CAMERA OFFLINE") -> None:
        super().__init__(placeholder)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 320)
        self.setObjectName("cameraView")
        self._pixmap: QPixmap | None = None

    def set_frame(self, frame: object) -> None:
        if not isinstance(frame, np.ndarray) or frame.size == 0:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(image)
        self._rescale()

    def clear_frame(self, text: str = "CAMERA OFFLINE") -> None:
        self._pixmap = None
        self.clear()
        self.setText(text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self) -> None:
        if self._pixmap is None:
            return
        self.setPixmap(
            self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
