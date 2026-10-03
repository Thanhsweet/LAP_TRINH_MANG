"""
HỌC PHẦN: LẬP TRÌNH MẠNG (NETWORK PROGRAMMING)
BÀI TẬP THỰC HÀNH SỐ 2 - CHƯƠNG 2: LẬP TRÌNH SOCKET VỚI PYTHON
Nhóm thực hiện      : Nhóm 05
Cổng dịch vụ nhóm   : 9005
Tệp nguồn           : echo_client.py
Mô tả chức năng     : TCP Client gửi chuỗi ký tự, kiểm tra IP thực tế qua socket
Hướng dẫn thực thi  : python echo_client.py
"""

import socket
import sys

SERVER_IP = "172.20.10.2"  # Thay bằng IP mạng LAN của máy Server khi chạy 2 máy
PORT = 9005


def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        try:
            print(f"[*] Đang kết nối tới {SERVER_IP}:{PORT}...")
            s.connect((SERVER_IP, PORT))
            print("[+] Kết nối thành công!")
            # In thông tin địa chỉ và cổng thực tế được OS xác nhận
            print(f"    - IP/Port Client tự cấp (getsockname): {s.getsockname()}")
            print(
                f"    - IP/Port Server thực tế nối tới (getpeername): {s.getpeername()}\n"
            )
        except ConnectionRefusedError as e:
            print(f"[!] Lỗi kết nối: {e}")
            print("[!] Lỗi: Server chưa chạy hoặc sai cổng!")
            sys.exit(1)
        except socket.timeout:
            print("[!] Lỗi: Quá thời gian chờ kết nối (timed out)!")
            sys.exit(1)
        except Exception as e:
            print(f"[!] Lỗi kết nối: {e}")
            sys.exit(1)

        while True:
            print("=" * 60)
            print("GỢI Ý THỰC HIỆN THÍ NGHIỆM (c):")
            print(" - Nhập câu tiếng Việt: Đại học Sư phạm Đà Nẵng")
            print(" - Nhập lệnh '5000'    : Tự động gửi chuỗi 5000 ký tự 'A'")
            print(" - Nhấn phím Enter    : Thoát chương trình")
            print("=" * 60)

            msg = input("Nhập dữ liệu gửi: ").strip()
            if not msg:
                print("[*] Đang đóng kết nối...")
                break

            # Tự động sinh chuỗi 5000 ký tự nếu nhập '5000'
            if msg == "5000":
                msg = "A" * 5000

            # 1. So sánh len(text) và len(text.encode("utf-8"))
            msg_bytes = msg.encode("utf-8")
            print(f"\n--- KẾT QUẢ ĐO ĐẠC ---")
            print(f"[*] Số ký tự chuỗi  (len(text))        : {len(msg)} ký tự")
            print(
                f"[*] Số bytes mã hóa (len(text.encode)): {len(msg_bytes)} bytes"
            )

            # Gửi toàn bộ dữ liệu đi
            s.sendall(msg_bytes)

            # 2. Đếm số lần gọi recv(1024) để nhận đủ dữ liệu
            received_bytes = b""
            recv_count = 0

            while len(received_bytes) < len(msg_bytes):
                chunk = s.recv(1024)
                if not chunk:
                    print("[!] Server đã đóng kết nối đột ngột.")
                    break
                recv_count += 1
                received_bytes += chunk
                print(
                    f"    -> Lần recv(1024) thứ {recv_count}: nhận được {len(chunk)} bytes"
                )

            print(f"[*] Tổng số lần client gọi recv(1024): {recv_count} lần")
            print(
                f"[*] Tổng số bytes nhận về đầy đủ   : {len(received_bytes)} bytes"
            )
            if len(msg) <= 50:
                print(
                    f"[*] Dữ liệu phản hồi               : {received_bytes.decode('utf-8')}\n"
                )
            else:
                print(
                    f"[*] Dữ liệu phản hồi               : [Chuỗi 5000 ký tự đã nhận đủ]\n"
                )


if __name__ == "__main__":
    run_client()