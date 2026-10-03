"""
Tệp: phia_nhan.py
Môn học: Lập trình mạng 
Nhóm: 05 - Lớp: 24CNTT3
Thành viên thực hiện: Đặng Nhật Thanh
Mô tả: Thí nghiệm dính gói - tách gói TCP
Lệnh chạy: python phia_nhan.py --host 0.0.0.0 --port 9005
"""

import argparse
import socket
import time


def main():
    parser = argparse.ArgumentParser(
        description="Phía nhận - Thí nghiệm dính gói/tách gói TCP"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9005)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.host, args.port))
        srv.listen(1)

        print(f"Đang lắng nghe tại {args.host}:{args.port}")
        print("Chờ phía gửi kết nối...")

        conn, addr = srv.accept()

        with conn:
            print(f"Đã kết nối với: {addr}")

            # Theo đúng khung đề:
            # cố tình chờ 1 giây trước khi bắt đầu đọc.
            print("Chờ 1 giây trước khi recv()...")
            time.sleep(1)

            # Lần recv đầu tiên chỉ lấy tối đa 60 byte.
            dau = conn.recv(60)

            print()
            print("--- 60 BYTE ĐẦU TIÊN ---")
            print(repr(dau))
            print()

            tong = len(dau)
            lan = 1

            # Tiếp tục đọc cho đến khi phía gửi đóng socket.
            while True:
                chunk = conn.recv(65536)

                if not chunk:
                    break

                tong += len(chunk)
                lan += 1

            print("-" * 70)
            print("KẾT QUẢ")
            print(f"60 byte đầu tiên : {repr(dau)}")
            print(f"Tổng dữ liệu     : {tong:,} byte")
            print(f"Tổng số recv()   : {lan} lần")


if __name__ == "__main__":
    main()