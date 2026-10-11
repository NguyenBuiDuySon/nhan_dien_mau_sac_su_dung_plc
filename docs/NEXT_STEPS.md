# Next steps

1. Recreate DB100/DB101 in TIA Portal and test read-only status first.
2. Confirm exact S7-1200 CPU, firmware, TIA Portal version and axis hardware.
3. Configure X/Y/Z Technology Objects in mm, homing and software limits.
4. Port V03 ROI/background/presence/stability pipeline into a dedicated VisionService.
5. Add Color CRUD dialogs without coupling Color to Destination.
6. Add command AckSeq checking and Vision ResultSeq/AckSeq handshake.
7. Add persistent production counters and alarm history.

## Stage 3 UI refinement

- Sidebar tăng chiều rộng và font để gần mockup công nghiệp hơn.
- Overview không hiển thị số liệu giả cho phần cứng chưa có feedback.
- Băng tải hiện chỉ hiển thị RUN/STOP command nếu chưa có encoder/drive feedback.
- Vacuum hiện chỉ hiển thị ON/OFF output; áp suất để "Không đo" khi chưa có pressure sensor.
- Vị trí XYZ được ghi rõ là vị trí PLC tính toán sau Homing khi hệ thống chưa có encoder.
- Icon Unicode hiện chỉ là placeholder. Bước UI polish cuối sẽ chuyển sang SVG đồng bộ.
