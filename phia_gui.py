"""
Tệp: phia_gui.py
Môn học: Lập trình mạng 
Nhóm: 05 - Lớp: 24CNTT3
Thành viên thực hiện: Đặng Nhật Thanh
Mô tả: Phía gửi cho thí nghiệm dính gói - tách gói TCP
Lệnh chạy: python phia_gui.py --host IP-MÁY-1 --port 9005
"""

import argparse
import socket
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Phía gửi - Thí nghiệm dính gói/tách gói TCP"
    )
    parser.add_argument("--host", default="10.243.59.89")
    parser.add_argument("--port", type=int, default=9005)
    args = parser.parse_args()
    data_5mb = Path(__file__).with_name("data_5mb.txt").read_bytes()

    with socket.create_connection((args.host, args.port), timeout=5.0) as s:
        print(f"Đã kết nối tới {args.host}:{args.port}")

        # Gửi liên tiếp ba thông điệp ngắn.
        for i in range(1, 4):
            data = f"MSG|all|tin {i}\n".encode("utf-8")
            s.sendall(data)
            print(f"Đã gửi: {data!r}")

        # Sau đó gửi khối 5 MB.
        # data_5mb = b"x" * 5_000_000
        print(f"Đang gửi khối {len(data_5mb):,} byte...")
        s.sendall(data_5mb)

        print("Đã gửi xong 5 MB.")
        print("Đóng socket để phía nhận phát hiện EOF.")


if __name__ == "__main__":
    main()
