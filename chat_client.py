"""
Tệp: chat_client.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên thực hiện: Lê Văn Bình
Bổ sung thí nghiệm tính tuần tự: Đặng Nhật Thanh

Mô tả:
- TCP Chat Client dòng lệnh.
- Hỗ trợ LOGIN, MSG, HISTORY, QUIT.
- Thí nghiệm đo tính tuần tự của server

Lệnh chạy: python chat_client.py --host 127.0.0.1 --port 9005

Lệnh chạy Client B để đo tính tuần tự: python chat_client.py --host 127.0.0.1 --port 9005 --m --name ClientB
"""

import argparse
import socket
import time
from datetime import datetime

from protocol import recv_line, send_line


def now_text():
    """
    Trả về thời gian hiện tại 
    """
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def recv_response(sock: socket.socket, buf: bytes):
  

    line, buf = recv_line(sock, buf)

    # Ghi nhận thời điểm phản hồi đầu tiên vừa tới.
    response_time = time.perf_counter()
    response_text = now_text()

    if line is None:
        raise ConnectionError("Server đã ngắt kết nối.")

    first_line = line

    # Tương thích cả HISTORY_ACK|n và HISTORY|n
    if line.startswith("HISTORY_ACK|") or line.startswith("HISTORY|"):
        try:
            n = int(line.split("|", 1)[1])
        except ValueError:
            print("Lỗi: Server gửi thông điệp HISTORY không hợp lệ.")
            return buf, first_line, response_time, response_text

        print(line)

        # Đọc chính xác n dòng nội dung tiếp theo.
        for _ in range(n):
            history_line, buf = recv_line(sock, buf)

            if history_line is None:
                raise ConnectionError(
                    "Mất kết nối khi đang nhận lịch sử chat."
                )

            print(history_line)

    else:
        print(line)

    return buf, first_line, response_time, response_text


def run_measurement(sock: socket.socket, buf: bytes, username: str,
                    t_connect_perf: float, t_connect_text: str):

    """Đo tính tuần tự"""

    command = f"LOGIN|{username}"

    print()
    print("THÍ NGHIỆM ĐO TÍNH TUẦN TỰ - CLIENT B")
    print(f"t_connect  = {t_connect_text}")
    print(f"Gửi        = {command}")

    # Gửi LOGIN ngay sau connect
    send_line(sock, command)

    try:
        buf, first_line, t_response_perf, t_response_text = recv_response(
            sock, buf
        )

    except TimeoutError:
        print()
        print("[LỖI] Quá thời gian chờ phản hồi từ server.")
        print(
            "Client A có thể đang giữ phiên quá lâu hoặc server gặp sự cố."
        )
        return buf, False

    delta = t_response_perf - t_connect_perf

    print()
    print("KẾT QUẢ ĐO")
    print(f"t_connect  : {t_connect_text}")
    print(f"t_response : {t_response_text}")
    print(f"Δt         : {delta:.3f} giây")

    print("-" * 65)
    print(f"Phản hồi: {first_line}")

    if first_line.startswith("OK|"):
        print()
        print(
            "Client B đã connect "
        )
        logged_in = True
    else:
        print()
        print(
            "LƯU Ý: Client B không LOGIN thành công. "
            "Kiểm tra tên đăng nhập hoặc trạng thái server."
        )
        logged_in = False

    print("-" * 65)
    print()

    return buf, logged_in


def main():
    parser = argparse.ArgumentParser(
        description="Chat Client - Nhóm 05"
    )

    parser.add_argument(
        "--host",
        default="10.243.59.89",
        help="Địa chỉ server"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=9005,
        help="Cổng server"
    )

    # Chế độ đo dành cho thí nghiệm hai Client.
    parser.add_argument(
        "--m",
        action="store_true",
        help=(
            "Đo t_connect, t_response và Δt "
            "để chứng minh Server tuần tự"
        )
    )

    # Username được tự động LOGIN khi chạy --measure.
    parser.add_argument(
        "--name",
        default="ClientB",
        help="Tên đăng nhập dùng khi chạy --measure"
    )

    args = parser.parse_args()

    if args.m:
        print("ĐO TÍNH TUẦN TỰ")
        print("Username:", args.name)

    sock = None

    try:
        # KẾT NỐI SERVER
        sock = socket.create_connection(
            (args.host, args.port),
            timeout=500.0
        )

        # Ghi thời điểm connect() vừa thành công.
        t_connect_perf = time.perf_counter()
        t_connect_text = now_text()

        if args.m:
            sock.settimeout(500.0)
        else:
            sock.settimeout(500.0)

        print("Đã kết nối server.")
        buf = b""

        # CHẾ ĐỘ ĐO TÍNH TUẦN TỰ

        if args.m:
            buf, logged_in = run_measurement(
                sock,
                buf,
                args.name,
                t_connect_perf,
                t_connect_text
            )

            if not logged_in:
                return

        else:
            print("Nhập lệnh, gõ Ctrl+C để thoát.")

        while True:
            try:
                command = input("> ")

                if not command:
                    continue

                # Gửi lệnh kèm ranh giới \n.
                send_line(sock, command)

                # Nhận phản hồi tương ứng.
                buf, _, _, _ = recv_response(sock, buf)

                # QUIT -> server trả BYE rồi đóng phiên.
                if command.strip() == "QUIT":
                    break

            except TimeoutError:
                print(
                    "Lỗi: Server phản hồi quá thời gian. "
                    "Kiểm tra server hoặc kết nối mạng."
                )

            except ConnectionError as e:
                print(
                    f"Lỗi kết nối: {e}. "
                    "Kiểm tra server có đang chạy không."
                )
                break

            except (EOFError, KeyboardInterrupt):
                print("\nĐã thoát client bằng Ctrl+C.")
                break

    except ConnectionRefusedError:
        print(
            "Không thể kết nối server: "
            "Server chưa chạy hoặc sai host/port."
        )

    except TimeoutError:
        print(
            "Kết nối server bị timeout. "
            "Kiểm tra địa chỉ và cổng server."
        )

    except ConnectionError as e:
        print(f"Lỗi kết nối: {e}")

    finally:
        if sock:
            try:
                sock.close()
            except OSError:
                pass


if __name__ == "__main__":
    main()