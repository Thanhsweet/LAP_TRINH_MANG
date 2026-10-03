"""
HỌC PHẦN: LẬP TRÌNH MẠNG (NETWORK PROGRAMMING)
BÀI TẬP THỰC HÀNH SỐ 2 - CHƯƠNG 2: LẬP TRÌNH SOCKET VỚI PYTHON
Nhóm thực hiện      : Nhóm 05
Cổng dịch vụ nhóm   : 9005
Tệp nguồn           : chat_login_server.py
Mô tả chức năng     : TCP Client gửi chuỗi ký tự, kiểm tra IP thực tế qua socket
Hướng dẫn thực thi  : python chat_login_server.py
"""
import socket

HOST = ""
PORT = 9005  # Cổng Nhóm 05

active_users = set()

ERR_FORMAT = "1"     # Sai định dạng (rỗng, >20 ký tự, chứa '|')
ERR_EXISTS = "2"     # Tên đã tồn tại
ERR_SEQUENCE = "3"   # Gửi lệnh khác khi chưa LOGIN

def recv_line(sock, buf=b""):
    while b"\n" not in buf:
        chunk = sock.recv(1024)
        if not chunk:
            return None, buf
        buf += chunk
    line, _, rest = buf.partition(b"\n")
    return line.decode("utf-8"), rest

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[*] SERVER CHAT LOGIN (TUẦN TỰ) ĐANG CHẠY TẠI CỔNG {PORT}...")

        while True:
            conn, addr = s.accept()
            print(f"\n[+] Tiếp nhận kết nối từ: {addr}")
            
            with conn:
                buf = b""
                logged_in_user = None

                while True:
                    line, buf = recv_line(conn, buf)
                    if line is None:
                        print(f"[-] Client {addr} đã đóng kết nối.")
                        break

                    line = line.strip()
                    if not line:
                        continue

                    print(f"    <- Nhận từ {addr}: {repr(line)}")

                    if line == "QUIT":
                        conn.sendall(b"OK|Tam biet\n")
                        break

                    # Xử lý LOGIN
                    if line.startswith("LOGIN|"):
                        name = line[6:]  # Lấy phần sau 'LOGIN|'
                        if len(name) == 0:
                            resp = f"ERR|{ERR_FORMAT}|Ten khong duoc de trong\n"
                        elif len(name) > 20:
                            resp = f"ERR|{ERR_FORMAT}|Ten khong duoc qua 20 ky tu\n"
                        elif "|" in name:
                            resp = f"ERR|{ERR_FORMAT}|Ten chua ky tu cam\n"
                        elif name in active_users:
                            resp = f"ERR|{ERR_EXISTS}|Ten da ton tai\n"
                        else:
                            logged_in_user = name
                            active_users.add(name)
                            resp = f"OK|Chào {name}\n"
                            print(f"[+] User [{name}] đăng nhập thành công. Active users: {active_users}")
                        conn.sendall(resp.encode("utf-8"))
                    else:
                        resp = f"ERR|{ERR_SEQUENCE}|Phai LOGIN truoc khi thuc hien lenh khac\n"
                        conn.sendall(resp.encode("utf-8"))

                if logged_in_user and logged_in_user in active_users:
                    # active_users.remove(logged_in_user)
                    print(f"[-] Đã giải phóng user [{logged_in_user}]. Active users: {active_users}")
            
            print(f"[*] Hoàn tất phiên {addr}. Chờ client tiếp theo...")

if __name__ == "__main__":
    run_server()