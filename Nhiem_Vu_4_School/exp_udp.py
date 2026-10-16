"""
Tệp: exp_udp.py
Phần C1 - Thí nghiệm mất gói và gửi lại UDP.

Cách chạy C1:
    Terminal 1:
        python udp_chat_server.py --loss 0.1
    Terminal 2:
        python exp_udp.py loss --port 9005 --p 0.1
Cách chạy C2:
    Terminal 1:
        Đo không mã yêu cầu: python exp_udp.py dup --port 9005
    Terminal 2:
        Đo có mã yêu cầu: python exp_udp.py dup --port 9005 --with-id    
Sau đó thực hiện tương tự với p = 0.3 và p = 0.5.

Yêu cầu:
- 1000 yêu cầu PING|i -> PONG|i
- timeout ban đầu 0.02 giây
- tối đa 4 lần gửi
- thời gian chờ: 0.02 -> 0.04 -> 0.08 -> 0.16 giây
- Đếm CHÍNH XÁC yêu cầu hoàn thành sau lần gửi thứ 1, 2, 3, 4.
- Chỉ chạy trên 127.0.0.1.
"""

import argparse
import socket
import time
import threading

N = 1000
FIRST_TIMEOUT = 0.02
MAX_TRIES = 4

def ask_count_attempt(sock, msg, expected, first_timeout=FIRST_TIMEOUT, max_tries=MAX_TRIES):
    """
    Gửi một yêu cầu UDP và trả về số lần SEND thực tế cần để nhận đúng phản hồi.
    """
    data = (msg + "\n").encode("utf-8")
    timeout = first_timeout
    old_timeout = sock.gettimeout()

    try:
        for attempt in range(1, max_tries + 1):
            sock.send(data)
            deadline = time.monotonic() + timeout

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break

                sock.settimeout(remaining)

                try:
                    reply = sock.recv(2048)
                except socket.timeout:
                    break

                line = reply.decode("utf-8", errors="replace").rstrip("\r\n")

                if line == expected:
                    return attempt

            timeout *= 2

        return None

    finally:
        sock.settimeout(old_timeout)

def run_loss(host, port, p):
    counts = [0, 0, 0, 0]
    failed = 0

    print("=" * 70)
    print("          THÍ NGHIỆM C1 - MẤT GÓI VÀ GỬI LẠI UDP")
    print("=" * 70)
    print(f"Server       : {host}:{port}")
    print(f"Mức loss     : p = {p}")
    print(f"Số yêu cầu   : {N}")
    print("Timeout      : 0.02 -> 0.04 -> 0.08 -> 0.16 giây")
    print(f"Tối đa gửi   : {MAX_TRIES} lần")
    print("=" * 70)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((host, port))

    start_all = time.monotonic()

    try:
        for i in range(1, N + 1):
            msg = f"PING|{i}"
            expected = f"PONG|{i}"

            try:
                attempt = ask_count_attempt(sock, msg, expected)

                if attempt is None:
                    failed += 1
                else:
                    counts[attempt - 1] += 1

            except (OSError, ConnectionRefusedError):
                failed += 1

    finally:
        sock.close()

    elapsed = time.monotonic() - start_all

    print()
    print("=" * 70)
    print("                         KẾT QUẢ")
    print("=" * 70)
    print(f"Hoàn thành lần 1 : {counts[0]}")
    print(f"Hoàn thành lần 2 : {counts[1]}")
    print(f"Hoàn thành lần 3 : {counts[2]}")
    print(f"Hoàn thành lần 4 : {counts[3]}")
    print(f"Thất bại         : {failed}")
    print("-" * 70)
    print(f"Tổng hoàn thành  : {sum(counts)}")
    print(f"Tổng yêu cầu     : {N}")
    print(f"Kiểm tra tổng    : {sum(counts) + failed} = {N}")
    print(f"Thời gian chạy   : {elapsed:.2f} giây")
    print("=" * 70)


def run_dup(host, port, with_id):
    mode_name = "CÓ MÃ YÊU CẦU" if with_id else "KHÔNG CÓ MÃ YÊU CẦU"
    print("=" * 70)
    print(f"          THÍ NGHIỆM C2 - LẶP GÓI ({mode_name})")
    print("=" * 70)

    sock_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_a.connect((host, port))
    sock_b.connect((host, port))

    # Đăng nhập cho cả 2 Socket
    login_a = ask_count_attempt(sock_a, "LOGIN|UserA", "OK|Chào UserA", 0.5, 4)
    login_b = ask_count_attempt(sock_b, "LOGIN|UserB", "OK|Chào UserB", 0.5, 4)

    if not login_a or not login_b:
        print("Lỗi: Socket A hoặc B không thể đăng nhập. Kiểm tra lại Server.")
        return

    b_stats = {'received': 0}
    b_running = True

    def listen_b():
        sock_b.settimeout(1.0)
        while b_running:
            try:
                data = sock_b.recv(4096)
                text = data.decode('utf-8')
                # Chỉ đếm tin nhắn được đẩy tới từ UserA
                if text.startswith("FROM|UserA|"):
                    b_stats['received'] += 1
            except socket.timeout:
                continue
            except OSError:
                break

    t = threading.Thread(target=listen_b, daemon=True)
    t.start()

    a_resends = 0
    a_fails = 0
    a_success = 0

    # A bắt đầu gửi 100 tin
    for i in range(1, 101):
        if with_id:
            msg = f"{i}|MSG|all|Tin {i}"
            expected = f"{i}|OK|Đã gửi"
        else:
            msg = f"MSG|all|Tin {i}"
            expected = "OK|Đã gửi"

        attempt = ask_count_attempt(sock_a, msg, expected)

        if attempt is None:
            a_fails += 1
        else:
            a_success += 1
            a_resends += (attempt - 1)

    # Đợi Socket B nhận nốt các gói tin đang trễ
    time.sleep(1.5)
    b_running = False
    sock_a.send(b"QUIT\n")
    sock_b.send(b"QUIT\n")
    sock_a.close()
    sock_b.close()

    duplicates = max(0, b_stats['received'] - a_success)

    print("\n=== KẾT QUẢ THÍ NGHIỆM LẶP GÓI (BẢNG 4) ===")
    print(f"Số lần A phải gửi lại     : {a_resends}")
    print(f"Số tin A báo thất bại     : {a_fails}")
    print(f"Số tin FROM B nhận được   : {b_stats['received']}")
    print(f"Số tin bị lặp ở B         : {duplicates}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Công cụ đo đạc các lỗi UDP (Phần C)"
    )

    sub = parser.add_subparsers(dest="mode", required=True)

    # Đăng ký lệnh loss (Lỗi 1)
    loss = sub.add_parser("loss", help="Đo mất gói và số lần gửi lại (Lỗi 1)")
    loss.add_argument("--host", default="127.0.0.1")
    loss.add_argument("--port", type=int, default=9005)
    loss.add_argument("--p", type=float, required=True,
                      help="Mức loss của Server: 0.1, 0.3 hoặc 0.5")

    # Đăng ký lệnh dup (Lỗi 2)
    dup = sub.add_parser("dup", help="Đo lặp gói và mã yêu cầu (Lỗi 2)")
    dup.add_argument("--host", default="127.0.0.1")
    dup.add_argument("--port", type=int, default=9005)
    dup.add_argument("--with-id", action="store_true", help="Có gắn mã yêu cầu chống lặp")

    args = parser.parse_args()

    if args.host != "127.0.0.1":
        parser.error("Phần C chỉ được chạy trên 127.0.0.1 theo yêu cầu đề.")

    if args.mode == "loss":
        if not 0 <= args.p <= 1:
            parser.error("--p phải nằm trong khoảng 0 đến 1")
        run_loss(args.host, args.port, args.p)
    elif args.mode == "dup":
        run_dup(args.host, args.port, args.with_id)

if __name__ == "__main__":
    main()