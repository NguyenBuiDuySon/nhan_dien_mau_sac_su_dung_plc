from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MachineMode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class MachineState(str, Enum):
    IDLE = "IDLE"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    HOMING = "HOMING"
    FAULT = "FAULT"


@dataclass(slots=True)
class AxisPosition:
    """Tọa độ máy theo đơn vị kỹ thuật mm.

    HMI và application luôn làm việc bằng mm. Nếu phần cứng dùng PTO/xung,
    việc quy đổi mm <-> pulse nằm trong Technology Object hoặc FB Motion của PLC.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(slots=True)
class PLCStatus:
    """Snapshot trạng thái do PLC xác nhận và HMI chỉ có nhiệm vụ hiển thị."""

    connected: bool = False
    mode: MachineMode = MachineMode.AUTO
    state: MachineState = MachineState.IDLE
    axes: AxisPosition = field(default_factory=AxisPosition)
    vacuum_on: bool = False
    conveyor_on: bool = False
    conveyor_speed: float = 0.0
    product_sensor: bool = False
    axis_homed: bool = False
    safety_ok: bool = True
    servo_ready: bool = True
    vacuum_ready: bool = True
    fault_code: int = 0

    @property
    def machine_ready(self) -> bool:
        return (
            self.connected
            and self.state in {MachineState.READY, MachineState.PAUSED}
            and self.axis_homed
            and self.safety_ok
            and self.servo_ready
            and self.fault_code == 0
        )
