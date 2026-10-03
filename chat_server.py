"""
Tệp: chat_server.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên: Bùi Xuân Khánh & Trần Quốc Trường
Lệnh chạy: python chat_server.py --host 0.0.0.0 --port 9005
"""

import argparse
import logging
import socket
from protocol import recv_line, send_line

# Cấu hình dữ liệu toàn cục
SYSTEM_NAMES = {"admin", "system", "server", "all"}
active_users = set()
chat_history = []

# Định nghĩa 7 mã lỗi theo thiết kế của Trường
ERR_FORMAT = "1"
ERR_EXISTS = "2"
ERR_SEQUENCE = "3"
ERR_INVALID_CMD = "4"
ERR_CONTENT = "5"
ERR_HISTORY = "6"
ERR_TARGET = "7"


def create_listener(host: str, port: int) -> socket.socket:
    """Khởi tạo socket lắng nghe tuần tự."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    return s


def handle_request(line: str, sess: dict) -> str:
    """Hàm xử lý logic phản hồi giao thức chat."""
    # 1. Lệnh QUIT
    if line == "QUIT":
        return "BYE"

    # 2. Lệnh LOGIN
    if line.startswith("LOGIN|") or line == "LOGIN":
        if sess["logged_in"]:
            return f"ERR|{ERR_SEQUENCE}|Ban da dang nhap roi"

        username = line[6:] if line.startswith("LOGIN|") else ""

        if len(username) == 0:
            return f"ERR|{ERR_FORMAT}|Ten khong duoc de trong"
        if len(username) > 20:
            return f"ERR|{ERR_FORMAT}|Ten khong duoc qua 20 ky tu"
        if "|" in username:
            return f"ERR|{ERR_FORMAT}|Ten khong duoc chua ky tu |"
        if username.lower() in SYSTEM_NAMES:
            return f"ERR|{ERR_EXISTS}|Ten he thong khong duoc su dung"
        if username in active_users:
            return f"ERR|{ERR_EXISTS}|Ten da ton tai hoac khong hop le"

        active_users.add(username)
        sess["logged_in"] = True
        sess["username"] = username
        return f"OK|Chao {username}"

    # 3. Lệnh không hợp lệ (Không thuộc MSG, HISTORY)
    if not (
        line.startswith("MSG|")
        or line.startswith("HISTORY|")
        or line == "MSG"
        or line == "HISTORY"
    ):
        return f"ERR|{ERR_INVALID_CMD}|Lenh khong hop le"

    # 4. Kiểm tra điều kiện phải đăng nhập trước
    if not sess["logged_in"]:
        return f"ERR|{ERR_SEQUENCE}|Phai LOGIN truoc khi thuc hien lenh khac"

    # 5. Lệnh MSG
    if line.startswith("MSG|") or line == "MSG":
        parts = line.split("|", 2)
        if len(parts) < 3:
            return f"ERR|{ERR_INVALID_CMD}|Lenh khong hop le"

        target, content = parts[1], parts[2]
        if target != "all":
            return f"ERR|{ERR_TARGET}|Chi ho tro gui den all"
        if content == "":
            return f"ERR|{ERR_CONTENT}|Noi dung khong duoc de trong"

        msg = f"{sess['username']} : {content}"
        chat_history.append(msg)
        return "OK|Da luu tin nhan"

    # 6. Lệnh HISTORY
    if line.startswith("HISTORY|") or line == "HISTORY":
        if line == "HISTORY":
            return f"ERR|{ERR_HISTORY}|HISTORY phai la so nguyen duong"

        arg = line[8:]
        if not arg.isdigit() or int(arg) <= 0:
            return f"ERR|{ERR_HISTORY}|HISTORY phai la so nguyen duong"

        n = int(arg)
        messages = chat_history[max(0, len(chat_history) - n) :]

        lines = [f"HISTORY_ACK|{len(messages)}"]
        lines.extend(messages)
        return "\n".join(lines)

    return f"ERR|{ERR_INVALID_CMD}|Lenh khong hop le"


def handle_client(conn: socket.socket, addr):
    """Xử lý phiên kết nối của một client."""
    sess = {"logged_in": False, "username": None}
    buf = b""
    try:
        while True:
            line, buf = recv_line(conn, buf)
            if line is None:
                break

            logging.info("%s:%d >> %s", addr[0], addr[1], line)
            reply = handle_request(line, sess)
            send_line(conn, reply)

            if reply == "BYE":
                break
    except (OSError, ValueError) as e:
        logging.warning("Lỗi phiên với %s:%d: %s", *addr, e)
    finally:
        if sess["username"]:
            active_users.discard(sess["username"])
            logging.info("Đã dọn dẹp user '%s' khỏi danh sách online", sess["username"])
        conn.close()


def serve_forever(listener: socket.socket):
    """Vòng lặp lắng nghe tuần tự phục vụ từng client một."""
    listener.settimeout(1.0)
    while True:
        try:
            conn, addr = listener.accept()
        except TimeoutError:
            continue

        logging.info("Tiếp nhận kết nối từ %s:%d", *addr)
        conn.settimeout(300.0)
        handle_client(conn, addr)
        logging.info("Đóng phiên phục vụ %s:%d", *addr)


def main():
    parser = argparse.ArgumentParser(description="TCP Chat Server Tuần Tự - Nhóm 05")
    parser.add_argument("--host", default="0.0.0.0", help="Host bind (mặc định 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9005, help="Port lắng nghe (mặc định 9005)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        listener = create_listener(args.host, args.port)
    except OSError as e:
        raise SystemExit(f"Không thể mở cổng {args.port}: {e}")

    logging.info("Server đang lắng nghe tại %s:%d (Mô hình tuần tự)", args.host, args.port)
    with listener:
        try:
            serve_forever(listener)
        except KeyboardInterrupt:
            logging.info("Dừng server an toàn (Ctrl+C)")


if __name__ == "__main__":
    main()