# Kiến trúc V04 PLC

## Nguyên tắc chính

V04 tách 3 khái niệm: **Color**, **Routing**, **Destination**.

```text
Vision -> Color ID -> RoutingService -> Destination -> PLC -> Pick & Place
```

- `ColorProfile`: chỉ chứa thông tin nhận diện (HSV, tên, trạng thái).
- `Destination`: chỉ chứa vị trí cơ khí X/Y/Z.
- `RoutingRule`: ánh xạ một màu sang một Destination.
- Nhiều màu có thể cùng trỏ tới một Destination.

## Ranh giới PLC

PLC không cần biết HSV hoặc tên màu. PC giải quyết Routing trước; PLC chỉ cần nhận
job/đích và chịu trách nhiệm machine state, interlock, motion, vacuum, conveyor, alarm.

Stage 1 dùng `MockPLCService` để xây HMI mà chưa phụ thuộc phần cứng.
