# Kiểm tra V04 với S7-1200 / TIA Portal V16

TIA Portal V16 chỉ là môi trường engineering. Khả năng HMI Python giao tiếp được hay không phụ thuộc chủ yếu vào CPU S7-1200, firmware, protection level, PUT/GET và layout DB.

## 1. Cấu hình TIA

- CPU có IP cùng subnet với PC.
- Bật **Permit access with PUT/GET communication from remote partner**.
- DB100 và DB101 dùng **standard / non-optimized access** để offset byte ổn định.
- Rack = 0, Slot = 1 cho S7-1200.
- Chỉ mở PUT/GET trên mạng lab/industrial được cô lập.

## 2. Test theo từng lớp

### Lớp A — Network

PC ping được PLC và TCP 102 không bị firewall chặn.

### Lớp B — S7 connection + DB read

Chạy:

```powershell
python tools/plc_v16_probe.py --ip 192.168.0.10
```

PASS khi script connect và đọc được DB101 đúng 32 byte.

### Lớp C — command/ack nhưng không chạy cơ cấu

Trong PLC, quy ước `CommandCode = 0` là NOP / Link Test:

1. Nếu `CommandSeq <> AckSeq` và `CommandCode = 0`, không điều khiển output.
2. Chỉ copy `AckSeq := CommandSeq`.

Sau đó chạy:

```powershell
python tools/plc_v16_probe.py --ip 192.168.0.10 --handshake
```

PASS khi `AckSeq` phản hồi đúng sequence HMI gửi.

### Lớp D — HMI thread / responsiveness

- Mở camera.
- Chuyển qua lại Overview / Auto / Manual liên tục.
- Rút cáp PLC 5-10 giây: HMI không treo, trạng thái chuyển Offline.
- Cắm lại: PLC polling thread tự reconnect.
- Camera vẫn cập nhật trong lúc PLC mất kết nối.

### Lớp E — Manual command không gắn tải

Trước khi nối motor/van thật, test PLC bằng các bit nội bộ:

- JOG X +5 mm -> PLC nhận đúng `AxisCode=1`, `ValueMm=5.0`.
- HOME -> PLC nhận đúng command và chuyển state HOMING.
- Vacuum ON/OFF -> chỉ cập nhật status bit test, chưa nối Q output.

Khi các bước trên pass mới map command sang Technology Object / Q output thật.

## 3. Tiêu chí pass cho V04

- HMI không block main thread khi PLC timeout.
- DB101 đọc ổn định theo chu kỳ polling.
- Mỗi command mới có sequence riêng.
- PLC chỉ ack sau khi nhận command mới.
- HMI không tự giả định RUNNING trước khi PLC trả state RUNNING.
- Khi mất PLC, Camera/UI vẫn hoạt động.
