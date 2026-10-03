"""
HỌC PHẦN: LẬP TRÌNH MẠNG (NETWORK PROGRAMMING)
BÀI TẬP THỰC HÀNH SỐ 2 - CHƯƠNG 2: LẬP TRÌNH SOCKET VỚI PYTHON
Nhóm thực hiện      : Nhóm 05
Cổng dịch vụ nhóm   : 9005
Tệp nguồn           : chat_login_client.py
Mô tả chức năng     : TCP Client gửi chuỗi ký tự, kiểm tra IP thực tế qua socket
Hướng dẫn thực thi  : python chat_login_client.py
"""
import socket

SERVER_IP = "127.0.0.1"
PORT = 9005

def recv_line(sock, buf=b""):
    while b"\n" not in buf:
        chunk = sock.recv(1024)
        if not chunk:
            return None, buf
        buf += chunk
    line, _, rest = buf.partition(b"\n")
    return line.decode("utf-8"), rest

def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            print(f"[*] Đang kết nối tới Server {SERVER_IP}:{PORT}...")
            s.connect((SERVER_IP, PORT))
            print("[+] Kết nối thành công!")
            
            buf = b""
            attempts = 0
            login_success = False

            while attempts < 3 and not login_success:
                attempts += 1
                name = input(f"\nNhập tên đăng nhập (Lần thử {attempts}/3): ").strip()
                
                msg = f"LOGIN|{name}\n"
                s.settimeout(5.0)  # Chỉ bật timeout khi gửi và nhận
                s.sendall(msg.encode("utf-8"))

                resp, buf = recv_line(s, buf)
                s.settimeout(None)  # Tắt timeout khi chờ người dùng nhập
                
                if resp is None:
                    print("[!] Server đã ngắt kết nối.")
                    return

                print(f"[SERVER PHẢN HỒI] -> {resp}")
                
                if resp.startswith("OK|"):
                    login_success = True
                    print("[v] ĐĂNG NHẬP THÀNH CÔNG!")
                elif resp.startswith("ERR|"):
                    parts = resp.split("|", 2)
                    err_code = parts[1] if len(parts) > 1 else "?"
                    err_desc = parts[2] if len(parts) > 2 else "Lỗi"
                    print(f"[x] Đăng nhập thất bại (Mã lỗi {err_code}): {err_desc}")

            if not login_success:
                print("\n[!] Bạn đã nhập sai quá 3 lần. Đóng kết nối!")
                s.sendall(b"QUIT\n")
            else:
                print("\n(Gõ 'QUIT' để thoát)")
                while True:
                    cmd = input("Lệnh tiếp theo > ").strip()
                    if not cmd:
                        continue
                    s.sendall((cmd + "\n").encode("utf-8"))
                    resp, buf = recv_line(s, buf)
                    print(f"[SERVER PHẢN HỒI] -> {resp}")
                    if cmd == "QUIT":
                        break

        except ConnectionRefusedError:
            print("[!] Lỗi: Server chưa chạy hoặc sai cổng!")
        except Exception as e:
            print(f"[!] Lỗi phát sinh: {e}")
        finally:
            print("[*] Đã đóng phiên làm việc.")

if __name__ == "__main__":
    run_client()