from __future__ import annotations

from copy import deepcopy

from domain.machine import AxisPosition, MachineMode, MachineState, PLCStatus
from services.plc_service import PLCService


class MockPLCService(PLCService):
    """PLC giả để xây HMI trước khi phần cứng/TIA hoàn thiện."""

    def __init__(self) -> None:
        self._status = PLCStatus(
            connected=True,
            state=MachineState.READY,
            axes=AxisPosition(0.0, 0.0, 0.0),
            axis_homed=True,
            safety_ok=True,
            servo_ready=True,
            vacuum_ready=True,
        )

    def get_status(self) -> PLCStatus:
        return deepcopy(self._status)

    def start_auto(self) -> None:
        if self._status.fault_code == 0 and self._status.mode == MachineMode.AUTO:
            self._status.state = MachineState.RUNNING
            self._status.conveyor_on = True

    def pause_auto(self) -> None:
        if self._status.state == MachineState.RUNNING:
            self._status.state = MachineState.PAUSED
            self._status.conveyor_on = False

    def stop(self) -> None:
        self._status.state = MachineState.READY
        self._status.conveyor_on = False
        self._status.vacuum_on = False

    def reset(self) -> None:
        self._status.fault_code = 0
        self._status.state = MachineState.READY

    def set_mode(self, mode: str) -> None:
        normalized = mode.strip().upper()
        self._status.mode = MachineMode.MANUAL if normalized == "MANUAL" else MachineMode.AUTO
        self.stop()

    def jog(self, axis: str, delta_mm: float) -> None:
        if self._status.mode != MachineMode.MANUAL:
            return
        axis = axis.lower()
        if axis not in {"x", "y", "z"}:
            raise ValueError("Axis phải là x, y hoặc z")
        current = getattr(self._status.axes, axis)
        # Machine coordinate của project: gốc = 0 và tọa độ làm việc không âm.
        setattr(self._status.axes, axis, max(0.0, current + delta_mm))

    def home_axis(self, axis: str | None = None) -> None:
        if axis is None:
            self._status.axes = AxisPosition()
        else:
            key = axis.lower()
            if key not in {"x", "y", "z"}:
                raise ValueError("Axis phải là x, y hoặc z")
            setattr(self._status.axes, key, 0.0)
        self._status.axis_homed = True

    def set_vacuum(self, enabled: bool) -> None:
        self._status.vacuum_on = bool(enabled)

    def set_conveyor(self, enabled: bool) -> None:
        self._status.conveyor_on = bool(enabled)

    def close(self) -> None:
        return
