# PLC communication contract — V04

V04 uses `python-snap7` classic S7/PUT-GET access. The HMI exchanges commands and status through two fixed-layout DBs. Do **not** force outputs directly from Python.

## TIA prerequisites

- S7-1200 PUT/GET access enabled.
- Exchange DBs must have stable byte offsets. For this integration, keep optimized block access disabled on the exchange DBs.
- PLC performs all safety, mode, homing, axis limit, actuator and sequence checks.

## DB100 — HMI_TO_PLC, 16 bytes

| Offset | Type | Name | Meaning |
|---:|---|---|---|
| 0 | DINT | CommandSeq | Increasing command sequence |
| 4 | INT | CommandCode | Command enum |
| 6 | INT | AxisCode | 0=none/all, 1=X, 2=Y, 3=Z |
| 8 | REAL | ValueMm | Relative distance / parameter in mm |
| 12 | INT | DestinationID | Sorting destination |
| 14 | INT | Reserved | Reserved |

Command codes: 0 NOP / Link Test, 1 Start Auto, 2 Pause, 3 Stop, 4 Reset, 5 Auto Mode, 6 Manual Mode, 10 Relative Jog, 11 Home, 20 Vacuum ON, 21 Vacuum OFF, 22 Conveyor ON, 23 Conveyor OFF, 30 Sort to Destination.

## DB101 — PLC_TO_HMI, 32 bytes

| Offset | Type | Name |
|---:|---|---|
| 0 | DINT | AckSeq |
| 4 | INT | ModeCode: 1 Auto, 2 Manual |
| 6 | INT | StateCode: 0 Idle, 1 Ready, 2 Running, 3 Paused, 4 Homing, 9 Fault |
| 8 | DINT | FaultCode |
| 12 | REAL | X_mm |
| 16 | REAL | Y_mm |
| 20 | REAL | Z_mm |
| 24 | DWORD | StatusFlags |
| 28 | REAL | ConveyorSpeed |

StatusFlags: bit0 Vacuum ON, bit1 Conveyor ON, bit2 Product Sensor, bit3 Axis Homed, bit4 Safety OK, bit5 Servo Ready, bit6 Vacuum Ready.

## Unit rule

PC/HMI and PLC application coordinates use **mm**. Pulse conversion belongs inside Siemens Technology Object / PLC motion layer. This keeps the UI, destination database and routing independent from motor microstep settings, screw lead or pulley changes.


## NOP / Link Test

`CommandCode = 0` là lệnh kiểm tra truyền thông an toàn. PLC không điều khiển cơ cấu; khi nhận `CommandSeq` mới thì chỉ cập nhật `AckSeq = CommandSeq`. Dùng lệnh này để xác nhận đường HMI -> PLC -> HMI trước khi test motion thật.
