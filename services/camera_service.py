from __future__ import annotations

from threading import Event, Lock

import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot


class CameraWorker(QObject):
    frame_ready = Signal(object)
    error_occurred = Signal(str)
    stopped = Signal()

    def __init__(self, source: int | str, width: int, height: int, fps: int) -> None:
        super().__init__()
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self._stop_event = Event()

    @Slot()
    def run(self) -> None:
        capture = cv2.VideoCapture(self.source)
        if not capture.isOpened():
            self.error_occurred.emit(f"Không mở được camera: {self.source}")
            self.stopped.emit()
            return

        if self.width > 0:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height > 0:
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if self.fps > 0:
            capture.set(cv2.CAP_PROP_FPS, self.fps)

        try:
            while not self._stop_event.is_set():
                ok, frame = capture.read()
                if not ok or frame is None:
                    self.error_occurred.emit("Camera không trả về frame")
                    break
                self.frame_ready.emit(frame)
        finally:
            capture.release()
            self.stopped.emit()

    def request_stop(self) -> None:
        self._stop_event.set()


class CameraService(QObject):
    """Một camera dùng chung cho toàn bộ HMI.

    AutoPage và VisionPage cùng nghe ``frame_ready``; không màn hình nào tự mở
    VideoCapture riêng nên tránh tranh chấp camera như V03 từng gặp.
    """

    frame_ready = Signal(object)
    running_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: CameraWorker | None = None
        self._latest_frame: np.ndarray | None = None
        self._frame_lock = Lock()
        self._running = False
        self._last_error = ""

    @property
    def running(self) -> bool:
        return self._running

    @property
    def last_error(self) -> str:
        return self._last_error

    def latest_frame(self) -> np.ndarray | None:
        with self._frame_lock:
            return None if self._latest_frame is None else self._latest_frame.copy()

    def start(self, source: int | str, width: int, height: int, fps: int = 30) -> None:
        if self._running:
            return
        self._last_error = ""
        self._thread = QThread()
        self._worker = CameraWorker(source, width, height, fps)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.frame_ready.connect(self._handle_frame)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.stopped.connect(self._handle_stopped)
        self._worker.stopped.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._running = True
        self.running_changed.emit(True)
        self._thread.start()

    def stop(self) -> None:
        worker = self._worker
        if worker is not None:
            worker.request_stop()

    def close(self) -> None:
        self.stop()
        thread = self._thread
        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait(1200)

    @Slot(object)
    def _handle_frame(self, frame: object) -> None:
        if isinstance(frame, np.ndarray):
            with self._frame_lock:
                self._latest_frame = frame.copy()
            self.frame_ready.emit(frame)

    @Slot(str)
    def _handle_error(self, message: str) -> None:
        self._last_error = message
        self.error_occurred.emit(message)

    @Slot()
    def _handle_stopped(self) -> None:
        self._running = False
        self.running_changed.emit(False)

    @Slot()
    def _cleanup_thread(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
