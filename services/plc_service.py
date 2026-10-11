from __future__ import annotations

from abc import ABC, abstractmethod

from domain.machine import PLCStatus


class PLCService(ABC):
    """Contract duy nhất giữa HMI/Application và phần điều khiển máy.

    UI không được biết driver đang là Mock hay Siemens S7. Nhờ vậy ta có thể
    xây giao diện và test luồng trước khi PLC thật/TIA Portal hoàn thiện.
    """

    @abstractmethod
    def get_status(self) -> PLCStatus: ...

    @abstractmethod
    def start_auto(self) -> None: ...

    @abstractmethod
    def pause_auto(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def set_mode(self, mode: str) -> None: ...

    @abstractmethod
    def jog(self, axis: str, delta_mm: float) -> None: ...

    @abstractmethod
    def home_axis(self, axis: str | None = None) -> None: ...

    @abstractmethod
    def set_vacuum(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_conveyor(self, enabled: bool) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
