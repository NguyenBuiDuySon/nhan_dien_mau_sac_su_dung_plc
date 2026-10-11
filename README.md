# Nhan_dien_san_pham_V04_PLC

V04 is a clean rebuild of V03 for a Siemens S7-1200 based machine. It reuses proven Vision ideas from V03 but separates UI, machine control, color profiles, routing and destinations.

## Stack

- Python 3.13
- PySide6 industrial desktop HMI
- OpenCV / NumPy camera + vision
- python-snap7 3.x for S7-1200 PUT/GET communication

## Architecture rule

`Vision -> Color -> Routing -> Destination -> PLC`

Colors do not own coordinates. Multiple colors can route to one Destination.

## Motion rule

All HMI/config coordinates use millimeters. PLC converts mm to pulse through the Siemens Motion Technology Object or one PLC motion conversion layer. Machine coordinates use origin 0 and normal operating positions >= 0.

## Current stage

- Industrial six-page HMI rebuilt close to the approved mockups.
- Shared CameraService for Auto + Vision.
- Dynamic counters from ColorRepository.
- Editable HSV ranges.
- Editable Destination coordinates and many-colors-to-one-Destination routing.
- Mock PLC driver.
- Siemens S7 driver scaffold with documented DB100/DB101 contract.

See `docs/PLC_DB_CONTRACT.md` before enabling `plc.driver = "s7"`.

## Stage 4

- Sidebar được tăng font/khoảng cách để gần mockup công nghiệp hơn.
- Overview được chỉnh lại theo bố cục 5 card + camera/counter/status + axis/alarm.
- Không hiển thị tốc độ băng tải hay áp suất vacuum giả khi chưa có sensor.
- Thêm `tools/plc_v16_probe.py` và `docs/PLC_V16_ACCEPTANCE_TEST.md` để test S7-1200/TIA V16 theo từng lớp mà chưa cần chạy cơ cấu thật.
