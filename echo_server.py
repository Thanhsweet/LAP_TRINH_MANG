"""
HỌC PHẦN: LẬP TRÌNH MẠNG (NETWORK PROGRAMMING)
BÀI TẬP THỰC HÀNH SỐ 2 - CHƯƠNG 2: LẬP TRÌNH SOCKET VỚI PYTHON
Nhóm thực hiện      : Nhóm 05
Cổng dịch vụ nhóm   : 9005
Tệp nguồn           : echo_server.py
Mô tả chức năng     : TCP Client gửi chuỗi ký tự, kiểm tra IP thực tế qua socket
Hướng dẫn thực thi  : python echo_server.py
"""
import socket

# Cấu hình cổng: 9000 + mã nhóm ZZ (thay đổi theo mã nhóm của bạn)
HOST = ""  # Lắng nghe trên mọi card mạng
PORT = 9005  # Ví dụ: Nhóm 05 dùng 9005


def run_server():
    # Sử dụng with cho socket lắng nghe
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Cho phép dùng lại cổng ngay lập tức, tránh lỗi TIME_WAIT
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[*] Server đang lắng nghe tại cổng {PORT}...")
        print(f"[*] Socket lắng nghe (s.getsockname()): {s.getsockname()}")

        while True:
            try:
                # accept() sinh ra socket phiên (conn) riêng biệt cho mỗi client
                conn, addr = s.accept()
                print(f"\n[+] Đã kết nối với client từ: {addr}")

                # Sử dụng with cho socket phiên để tự giải phóng
                with conn:
                    # In thông tin để so sánh socket lắng nghe và socket phiên
                    print(
                        f"    - Socket phiên cục bộ (conn.getsockname()): {conn.getsockname()}"
                    )
                    print(
                        f"    - Địa chỉ đối phương (conn.getpeername()): {conn.getpeername()}"
                    )

                    while True:
                        data = conn.recv(1024)
                        # Nhận b"" nghĩa là client đã chủ động ngắt kết nối (EOF)
                        if not data:
                            print(f"[-] Client {addr} đã ngắt kết nối.")
                            break

                        # In thông điệp nhận được dạng text UTF-8
                        msg = data.decode("utf-8")
                        print(f"    [Nhận từ {addr[1]}]: {msg}")

                        # Trả lại nguyên vẹn nội dung cho client (Echo)
                        conn.sendall(data)

            except KeyboardInterrupt:
                print("\n[!] Dừng server thủ công.")
                break
            except OSError as e:
                print(f"[!] Lỗi socket server: {e}")


if __name__ == "__main__":
    run_server()