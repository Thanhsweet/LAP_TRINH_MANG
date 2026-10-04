"""
Tệp: udp_chat_server.py
Nhóm thực hiện: Nhóm 05 (Cổng mặc định: 9005)
Thành viên: Bùi Xuân Khánh, Trương Quốc Anh & Trần Quốc Trường
Lệnh chạy mẫu:
    python udp_chat_server.py --port 9005
    python udp_chat_server.py --port 9005 --loss 0.3
    python udp_chat_server.py --port 9005 --reply-loss 0.3
Mô tả: Server phòng chat UDP đơn luồng phục vụ cả phòng, quản lý phiên theo (IP, Port),
       xử lý dọn client im lặng, hỗ trợ giả lập mất gói đến và mất câu trả lời,
       chống lặp gói dựa trên lưu vết (Mã_yêu_cầu, Câu_trả_lời).
Tham khảo: Slide Chương 4 (mục 4.2), mở rộng cơ chế chống lặp theo mục 4.4 và đề bài.
"""

import argparse
import logging
import random
import socket
import time
from protocol import MAX_DGRAM, recv_dgram, send_dgram

ROOM = "Phòng chat UDP - Nhóm 05"
RESERVED = {"all", "server", "admin"}
MAX_TEXT = 1000  # Giới hạn nội dung tin nhắn không quá 1000 byte

# Quản lý phiên: clients[(ip, port)] = {"name": str, "seen": float}
clients = {}

# Chống lặp gói (Idempotency): last_replies[(ip, port)] = (req_id, reply_text)
last_replies = {}


def create_socket(host: str, port: int) -> socket.socket:
    """Khởi tạo socket UDP và bind cổng, không dùng listen/accept."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    return sock


def names():
    """Trả về tập hợp tên người dùng đang online."""
    return {c["name"] for c in clients.values()}


def to_room(text: str, skip=None):
    """Tạo danh sách các tuple (thông điệp, địa chỉ) gửi cho cả phòng trừ địa chỉ skip."""
    return [(text, addr) for addr in clients if addr != skip]


def do_login(name: str, addr):
    """Xử lý lệnh LOGIN. Hỗ trợ tính lặp lại vô hại (idempotent)."""
    # Nếu địa chỉ này đã đăng nhập
    if addr in clients:
        if clients[addr]["name"] == name:
            return [(f"OK|Chào {name}", addr)]  # Gửi lại vô hại
        return [("ERR|3|Đã đăng nhập", addr)]

    # Kiểm tra tính hợp lệ của tên
    ok = 0 < len(name) <= 20 and name.isprintable()
    if not ok or "|" in name:
        return [("ERR|2|Tên không hợp lệ", addr)]
    if name.lower() in RESERVED or name in names():
        return [("ERR|1|Tên đã tồn tại", addr)]

    # Đăng nhập hợp lệ: thông báo cho cả phòng trước khi lưu client
    out = to_room(f"SYS|{name} vào phòng")
    clients[addr] = {"name": name, "seen": time.monotonic()}
    return [(f"OK|Chào {name}", addr)] + out


def do_msg(arg: str, sess: dict, addr):
    """Xử lý lệnh gửi tin nhắn MSG."""
    to, sep, text = arg.partition("|")
    if not sep or not text:
        return [("ERR|4|Thiếu người nhận hoặc nội dung", addr)]
    if len(text.encode("utf-8")) > MAX_TEXT:
        return [("ERR|4|Nội dung quá 1000 byte", addr)]

    push = f"FROM|{sess['name']}|{to}|{text}"
    if to == "all":
        return [("OK|Đã gửi", addr)] + to_room(push, skip=addr)

    # Gửi tin nhắn riêng
    for a, c in clients.items():
        if c["name"] == to:
            return [("OK|Đã gửi", addr), (push, a)]
    return [("ERR|5|Người nhận không trực tuyến", addr)]


def do_quit(addr):
    """Xử lý lệnh thoát QUIT."""
    sess = clients.pop(addr, None)
    last_replies.pop(addr, None)
    out = [("BYE", addr)]
    if sess:
        out += to_room(f"SYS|{sess['name']} đã rời phòng")
    return out


def handle_datagram(text: str, addr):
    """Xử lý logic 1 datagram vào -> trả về danh sách [(thông_điệp, địa_chỉ), ...].
    Hỗ trợ cả cú pháp thường (CMD|...) và cú pháp có mã yêu cầu (REQ_ID|CMD|...).
    """
    req_id = None
    core_text = text.strip()

    # Kiểm tra xem gói tin có gắn mã yêu cầu tăng dần dạng <mã>|... (Phần C)
    parts = core_text.split("|", 1)
    if len(parts) == 2 and parts[0].isdigit():
        req_id = parts[0]
        core_text = parts[1]

        # Kiểm tra chống lặp: nếu gặp lại đúng mã cũ từ cùng địa chỉ thì trả lại câu trả lời cũ
        if addr in last_replies and last_replies[addr][0] == req_id:
            old_reply = last_replies[addr][1]
            return [(old_reply, addr)]

    cmd, _, arg = core_text.partition("|")
    sess = clients.get(addr)
    if sess:
        sess["seen"] = time.monotonic()  # Cập nhật mốc thời gian còn sống

    out = []
    # 1. Các lệnh không yêu cầu đăng nhập
    if cmd == "DISCOVER":
        out = [(f"HERE|{ROOM}|{len(clients)}", addr)]
    elif cmd == "PING":
        out = [(f"PONG|{arg}", addr)]
    elif cmd == "LOGIN":
        out = do_login(arg, addr)
    elif cmd == "QUIT":
        out = do_quit(addr)
    # 2. Các lệnh bắt buộc phải đăng nhập trước
    elif sess is None:
        out = [("ERR|3|Chưa đăng nhập", addr)]
    elif cmd == "MSG":
        out = do_msg(arg, sess, addr)
    elif cmd == "WHO":
        user_list = ",".join(sorted(names()))
        out = [(f"WHO|{user_list}", addr)]
    else:
        out = [("ERR|4|Lệnh không hợp lệ", addr)]

    # Nếu có mã yêu cầu, gắn mã vào câu trả lời đầu tiên và lưu vào bộ nhớ đệm
    if req_id is not None and out:
        first_reply, target = out[0]
        indexed_reply = f"{req_id}|{first_reply}"
        out[0] = (indexed_reply, target)
        last_replies[addr] = (req_id, indexed_reply)

    return out

def reap_idle(sock: socket.socket, idle_limit: float):
    """Quét và xóa các client im lặng quá idle_limit giây."""
    now = time.monotonic()
    for addr, c in list(clients.items()):
        if now - c["seen"] > idle_limit:
            name = c["name"]
            del clients[addr]
            last_replies.pop(addr, None)
            logging.info("Hết giờ: %s (%s:%d)", name, *addr)
            deliver(sock, to_room(f"SYS|{name} mất liên lạc"))


def deliver(sock: socket.socket, out_list):
    """Gửi toàn bộ danh sách datagram, bắt mọi lỗi truyền để bảo vệ server."""
    for text, addr in out_list:
        try:
            send_dgram(sock, (text + "\n").encode("utf-8"), addr)
        except (OSError, ValueError) as e:
            logging.warning("Lỗi gửi tới %s:%d: %s", *addr, e)


def serve_forever(
    sock: socket.socket, loss: float = 0.0, reply_loss: float = 0.0, idle: float = 60.0
):
    """Vòng nhận datagram duy nhất phục vụ toàn bộ phòng chat."""
    sock.settimeout(1.0)
    while True:
        try:
            data, addr, bi_qua_gioi_han = recv_dgram(sock)
        except socket.timeout:
            reap_idle(sock, idle)
            continue
        except (OSError, ValueError) as e:
            logging.warning("Bỏ qua datagram lỗi từ mạng: %s", e)
            continue

        if bi_qua_gioi_han:
            logging.warning(
                "Bỏ qua datagram từ %s:%d vì vượt quá %d byte",
                *addr,
                MAX_DGRAM,
            )
            continue

        try:
            text = data.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            logging.warning("Bỏ qua datagram không phải UTF-8 từ %s:%d", *addr)
            continue

        # Giả lập mất gói tin gửi đến (--loss)
        if loss > 0.0 and random.random() < loss:
            logging.info("%s:%d >> %s [MẤT]", *addr, text)
            continue

        logging.info("%s:%d >> %s", *addr, text)
        out = handle_datagram(text, addr)

        # Giả lập mất gói tin trả lời người gửi (--reply-loss phục vụ Phần C)
        if out and reply_loss > 0.0 and random.random() < reply_loss:
            logging.info("%s:%d << %s [MẤT TRẢ LỜI]", *addr, out[0][0])
            out = out[1:]  # Loại bỏ câu trả lời cho người gửi, tin đẩy tới người khác vẫn đi

        deliver(sock, out)
        reap_idle(sock, idle)


def main():
    parser = argparse.ArgumentParser(description="UDP Chat Server - Nhóm 05")
    parser.add_argument("--host", default="0.0.0.0", help="Địa chỉ bind (mặc định 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9005, help="Cổng UDP của nhóm (mặc định 9005)")
    parser.add_argument("--idle", type=float, default=60.0, help="Thời gian client im lặng tối đa (s)")
    parser.add_argument("--loss", type=float, default=0.0, help="Tỉ lệ giả lập mất gói đến (vd: 0.3)")
    parser.add_argument("--reply-loss", type=float, default=0.0, help="Tỉ lệ giả lập mất câu trả lời (vd: 0.3)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        sock = create_socket(args.host, args.port)
    except OSError as e:
        raise SystemExit(f"Không thể mở cổng {args.port}: {e}")

    logging.info(
        "Server UDP Nhóm 05 đang lắng nghe tại %s:%d (loss=%.0f%%, reply_loss=%.0f%%, idle=%.0fs)",
        args.host,
        args.port,
        args.loss * 100,
        args.reply_loss * 100,
        args.idle,
    )

    with sock:
        try:
            serve_forever(sock, loss=args.loss, reply_loss=args.reply_loss, idle=args.idle)
        except KeyboardInterrupt:
            logging.info("Dừng server an toàn (Ctrl+C)")


if __name__ == "__main__":
    main()
