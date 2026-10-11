# Kế thừa từ V03

## Giữ và port ở Stage 2

- `core/camera_service.py`
- `core/vision_processor.py`
- `core/hsv_color_service.py`
- `core/stability_filter.py`
- `core/product_detector.py`
- ROI camera widget
- Color calibrator
- Product counter

## Viết lại/refactor

- `desktop_app/main_window.py`: tách thành 6 Page.
- `app_state.py`: PLC là nguồn trạng thái máy chính.
- Cơ chế `sync_machine_points_with_colors`: thay bằng Color -> Routing -> Destination.
- `gantry_service.py`: thay bằng PLCService/Motion contract.

## Không đưa vào runtime V04

- `serial_service.py` ESP32
- `network_service.py` ESP32 SoftAP/TCP
- firmware `.ino`

Các file này vẫn giữ ở V03 để tham khảo hành vi cũ.
