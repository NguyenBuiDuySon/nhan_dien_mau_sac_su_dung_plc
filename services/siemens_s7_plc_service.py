from __future__ import annotations

import struct
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from domain.machine import AxisPosition, MachineMode, MachineState, PLCStatus
from services.plc_service import PLCService


class PLCCommand(IntEnum):
    """Mã lệnh HMI -> PLC.

    HMI chỉ gửi yêu cầu. PLC phải kiểm tra Safety/Mode/Interlock rồi mới thực thi.
    """

    NONE = 0
    START_AUTO = 1
    PAUSE_AUTO = 2
    STOP = 3
    RESET = 4
    MODE_AUTO = 5
    MODE_MANUAL = 6
    JOG_RELATIVE = 10
    HOME = 11
    VACUUM_ON = 20
    VACUUM_OFF = 21
    CONVEYOR_ON = 22
    CONVEYOR_OFF = 23
    SORT_DESTINATION = 30


@dataclass(slots=True)
class S7ConnectionConfig:
    host: str = "192.168.0.10"
    rack: int = 0
    slot: int = 1
    tcp_port: int = 102
    command_db: int = 100
    status_db: int = 101
    poll_interval_s: float = 0.20


class SiemensS7PLCService(PLCService):
    """Driver S7-1200 dùng python-snap7 3.x (import name ``s7``).

    Thiết kế cố tình dùng 2 DB giao tiếp có offset cố định:
    - DB100: HMI -> PLC command mailbox.
    - DB101: PLC -> HMI status snapshot.

    Đây là giao tiếp mức *command/status*, không phải HMI force trực tiếp Q output.
    PLC vẫn là nơi quyết định interlock, homing, motion và safety.

    Lưu ý TIA Portal:
    - S7-1200 phải cho phép PUT/GET.
    - DB giao tiếp phải dùng layout truy cập được theo byte offset
      (tắt optimized block access cho DB exchange nếu cần).
    """

    STATUS_SIZE = 32
    COMMAND_SIZE = 16

    FLAG_VACUUM_ON = 1 << 0
    FLAG_CONVEYOR_ON = 1 << 1
    FLAG_PRODUCT_SENSOR = 1 << 2
    FLAG_AXIS_HOMED = 1 << 3
    FLAG_SAFETY_OK = 1 << 4
    FLAG_SERVO_READY = 1 << 5
    FLAG_VACUUM_READY = 1 << 6

    def __init__(self, config: S7ConnectionConfig) -> None:
        self.config = config
        self._status = PLCStatus(connected=False)
        self._lock = threading.RLock()
        self._client: Any | None = None
        self._stop_event = threading.Event()
        self._command_seq = 0
        self._last_error = ""

        self._worker = threading.Thread(
            target=self._poll_loop,
            name="S7-PLC-Poll",
            daemon=True,
        )
        self._worker.start()

    @property
    def last_error(self) -> str:
        with self._lock:
            return self._last_error

    def get_status(self) -> PLCStatus:
        with self._lock:
            return deepcopy(self._status)

    def start_auto(self) -> None:
        self._send_command(PLCCommand.START_AUTO)

    def pause_auto(self) -> None:
        self._send_command(PLCCommand.PAUSE_AUTO)

    def stop(self) -> None:
        self._send_command(PLCCommand.STOP)

    def reset(self) -> None:
        self._send_command(PLCCommand.RESET)

    def set_mode(self, mode: str) -> None:
        command = PLCCommand.MODE_MANUAL if mode.strip().upper() == "MANUAL" else PLCCommand.MODE_AUTO
        self._send_command(command)

    def jog(self, axis: str, delta_mm: float) -> None:
        axis_code = self._axis_code(axis)
        self._send_command(PLCCommand.JOG_RELATIVE, axis_code=axis_code, value_mm=float(delta_mm))

    def home_axis(self, axis: str | None = None) -> None:
        axis_code = 0 if axis is None else self._axis_code(axis)
        self._send_command(PLCCommand.HOME, axis_code=axis_code)

    def set_vacuum(self, enabled: bool) -> None:
        self._send_command(PLCCommand.VACUUM_ON if enabled else PLCCommand.VACUUM_OFF)

    def set_conveyor(self, enabled: bool) -> None:
        self._send_command(PLCCommand.CONVEYOR_ON if enabled else PLCCommand.CONVEYOR_OFF)

    def sort_to_destination(self, destination_id: int) -> None:
        self._send_command(PLCCommand.SORT_DESTINATION, destination_id=int(destination_id))

    def close(self) -> None:
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=1.5)
        with self._lock:
            client = self._client
            self._client = None
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._ensure_connected()
                self._read_status()
            except Exception as error:
                self._mark_disconnected(str(error))
                self._disconnect_client()
            self._stop_event.wait(max(0.05, self.config.poll_interval_s))

    def _ensure_connected(self) -> None:
        with self._lock:
            client = self._client

        if client is not None:
            try:
                if client.get_connected():
                    return
            except Exception:
                pass

        # Import bên trong để app vẫn chạy Mock mode khi python-snap7 chưa cài.
        from s7 import Client

        client = Client(auto_reconnect=True, max_retries=2, retry_delay=0.3)
        client.connect(
            self.config.host,
            self.config.rack,
            self.config.slot,
            tcp_port=self.config.tcp_port,
        )
        with self._lock:
            self._client = client
            self._last_error = ""

    def _read_status(self) -> None:
        with self._lock:
            client = self._client
        if client is None:
            raise RuntimeError("PLC client chưa kết nối")

        data = client.db_read(self.config.status_db, 0, self.STATUS_SIZE)
        ack_seq = struct.unpack_from(">i", data, 0)[0]
        mode_code = struct.unpack_from(">h", data, 4)[0]
        state_code = struct.unpack_from(">h", data, 6)[0]
        fault_code = struct.unpack_from(">i", data, 8)[0]
        x_mm = struct.unpack_from(">f", data, 12)[0]
        y_mm = struct.unpack_from(">f", data, 16)[0]
        z_mm = struct.unpack_from(">f", data, 20)[0]
        flags = struct.unpack_from(">I", data, 24)[0]
        conveyor_speed = struct.unpack_from(">f", data, 28)[0]

        # ack_seq hiện chưa cần hiển thị, nhưng đọc để DB contract rõ ràng và
        # sẵn sàng cho command/ack handshake ở stage integration.
        _ = ack_seq

        status = PLCStatus(
            connected=True,
            mode=self._decode_mode(mode_code),
            state=self._decode_state(state_code),
            axes=AxisPosition(x_mm, y_mm, z_mm),
            vacuum_on=bool(flags & self.FLAG_VACUUM_ON),
            conveyor_on=bool(flags & self.FLAG_CONVEYOR_ON),
            conveyor_speed=float(conveyor_speed),
            product_sensor=bool(flags & self.FLAG_PRODUCT_SENSOR),
            axis_homed=bool(flags & self.FLAG_AXIS_HOMED),
            safety_ok=bool(flags & self.FLAG_SAFETY_OK),
            servo_ready=bool(flags & self.FLAG_SERVO_READY),
            vacuum_ready=bool(flags & self.FLAG_VACUUM_READY),
            fault_code=int(fault_code),
        )
        with self._lock:
            self._status = status
            self._last_error = ""

    def _send_command(
        self,
        command: PLCCommand,
        *,
        axis_code: int = 0,
        value_mm: float = 0.0,
        destination_id: int = 0,
    ) -> None:
        with self._lock:
            client = self._client
            if client is None:
                return
            self._command_seq = (self._command_seq + 1) & 0x7FFFFFFF
            seq = self._command_seq

            payload = bytearray(self.COMMAND_SIZE)
            struct.pack_into(">i", payload, 0, seq)
            struct.pack_into(">h", payload, 4, int(command))
            struct.pack_into(">h", payload, 6, int(axis_code))
            struct.pack_into(">f", payload, 8, float(value_mm))
            struct.pack_into(">h", payload, 12, int(destination_id))
            struct.pack_into(">h", payload, 14, 0)

            try:
                client.db_write(self.config.command_db, 0, payload)
            except Exception as error:
                self._last_error = str(error)
                self._status.connected = False

    def _mark_disconnected(self, message: str) -> None:
        with self._lock:
            self._status.connected = False
            self._last_error = message

    def _disconnect_client(self) -> None:
        with self._lock:
            client = self._client
            self._client = None
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass

    @staticmethod
    def _axis_code(axis: str) -> int:
        mapping = {"x": 1, "y": 2, "z": 3}
        try:
            return mapping[axis.strip().lower()]
        except KeyError as error:
            raise ValueError("Axis phải là x, y hoặc z") from error

    @staticmethod
    def _decode_mode(code: int) -> MachineMode:
        return MachineMode.MANUAL if code == 2 else MachineMode.AUTO

    @staticmethod
    def _decode_state(code: int) -> MachineState:
        mapping = {
            0: MachineState.IDLE,
            1: MachineState.READY,
            2: MachineState.RUNNING,
            3: MachineState.PAUSED,
            4: MachineState.HOMING,
            9: MachineState.FAULT,
        }
        return mapping.get(code, MachineState.IDLE)
