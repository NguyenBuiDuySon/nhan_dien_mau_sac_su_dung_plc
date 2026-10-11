"""Kiểm tra đường truyền Python <-> S7-1200 theo DB contract V04.

Mặc định script chỉ đọc DB101 nên không làm chạy cơ cấu.
Tùy chọn --handshake ghi CommandCode=0 (NOP) vào DB100 để kiểm tra AckSeq.
Chỉ dùng --handshake sau khi PLC program đã xử lý code 0 là NOP/Link Test.
"""

from __future__ import annotations

import argparse
import struct
import time

from s7 import Client


STATUS_SIZE = 32
COMMAND_SIZE = 16


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S7-1200 V04 link probe")
    parser.add_argument("--ip", required=True, help="Địa chỉ IP PLC")
    parser.add_argument("--rack", type=int, default=0)
    parser.add_argument("--slot", type=int, default=1)
    parser.add_argument("--status-db", type=int, default=101)
    parser.add_argument("--command-db", type=int, default=100)
    parser.add_argument("--handshake", action="store_true")
    parser.add_argument("--timeout", type=float, default=2.0)
    return parser.parse_args()


def decode_status(data: bytes) -> dict[str, object]:
    return {
        "AckSeq": struct.unpack_from(">i", data, 0)[0],
        "ModeCode": struct.unpack_from(">h", data, 4)[0],
        "StateCode": struct.unpack_from(">h", data, 6)[0],
        "FaultCode": struct.unpack_from(">i", data, 8)[0],
        "X_mm": struct.unpack_from(">f", data, 12)[0],
        "Y_mm": struct.unpack_from(">f", data, 16)[0],
        "Z_mm": struct.unpack_from(">f", data, 20)[0],
        "StatusFlags": struct.unpack_from(">I", data, 24)[0],
        "ConveyorSpeed": struct.unpack_from(">f", data, 28)[0],
    }


def main() -> int:
    args = parse_args()
    client = Client(auto_reconnect=False)
    print(f"[1/4] Connect {args.ip} rack={args.rack} slot={args.slot} ...")
    client.connect(args.ip, args.rack, args.slot)
    print("      OK")

    print(f"[2/4] Read DB{args.status_db} 0..{STATUS_SIZE - 1} ...")
    status = decode_status(client.db_read(args.status_db, 0, STATUS_SIZE))
    print("      OK")
    for key, value in status.items():
        print(f"      {key:15s}: {value}")

    if not args.handshake:
        print("[3/4] Handshake skipped (read-only mode)")
        print("[4/4] PASS: TCP/S7 + DB read path hoạt động")
        client.disconnect()
        return 0

    previous_ack = int(status["AckSeq"])
    seq = previous_ack + 1 if previous_ack < 2_147_483_647 else 1
    payload = bytearray(COMMAND_SIZE)
    struct.pack_into(">i", payload, 0, seq)
    struct.pack_into(">h", payload, 4, 0)  # NOP / link test

    print(f"[3/4] Write NOP seq={seq} to DB{args.command_db} ...")
    client.db_write(args.command_db, 0, payload)

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        current = decode_status(client.db_read(args.status_db, 0, STATUS_SIZE))
        if int(current["AckSeq"]) == seq:
            print("      ACK received")
            print("[4/4] PASS: read + write + PLC ack flow hoạt động")
            client.disconnect()
            return 0
        time.sleep(0.05)

    print("      FAIL: PLC không phản hồi AckSeq trong thời gian chờ")
    client.disconnect()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
