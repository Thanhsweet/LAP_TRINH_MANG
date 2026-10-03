"""
Tệp: chat_client.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên thực hiện: Lê Văn Bình
"""

import argparse
import socket
from protocol import recv_line, send_line


def recv_response(sock: socket.socket, buf: bytes):
    """
    Nhận một response hoàn chỉnh từ server.
    Nếu response là HISTORY_ACK|n hoặc HISTORY|n: đọc chính xác n dòng tiếp theo.
    """
    line, buf = recv_line(sock, buf)
    if line is None:
        raise ConnectionError("Server đã ngắt kết nối.")

    # Tương thích cả giao thức chuẩn của Server (HISTORY_ACK|) lẫn server test (HISTORY|)
    if line.startswith("HISTORY_ACK|") or line.startswith("HISTORY|"):
        try:
            n = int(line.split("|", 1)[1])
        except ValueError:
            print("Lỗi: Server gửi thông điệp HISTORY không hợp lệ.")
            return buf

        print(line)

        # Đọc chính xác n dòng nội dung tiếp theo
        for _ in range(n):
            history_line, buf = recv_line(sock, buf)
            if history_line is None:
                raise ConnectionError("Mất kết nối khi đang nhận lịch sử chat.")
            print(history_line)
    else:
        print(line)

    return buf


def main():
    parser = argparse.ArgumentParser(description="Chat Client - Nhóm 05")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ server")
    parser.add_argument("--port", type=int, default=9005, help="Cổng server")
    args = parser.parse_args()

    print("=== CHAT CLIENT ===")
    print("Server:", args.host)
    print("Port:", args.port)

    sock = None
    try:
        # Kết nối tới server với timeout thiết lập kết nối ban đầu
        sock = socket.create_connection((args.host, args.port), timeout=5.0)
        # Thiết lập timeout cho các thao tác gửi/nhận tiếp theo
        sock.settimeout(5.0)

        print("Đã kết nối server.")
        print("Nhập lệnh, gõ Ctrl+C để thoát.")

        # Duy trì bộ đệm ngoài vòng lặp để bảo lưu ranh giới dòng byte stream
        buf = b""

        while True:
            try:
                command = input("> ")
                if not command:
                    continue

                # Gửi lệnh kèm ranh giới \n qua hàm chuẩn của protocol.py
                send_line(sock, command)

                # Nhận phản hồi tương ứng
                buf = recv_response(sock, buf)

                # Nếu là lệnh QUIT thì đóng vòng lặp thoát client
                if command.strip() == "QUIT":
                    break

            except TimeoutError:
                print(
                    "Lỗi: Server phản hồi quá thời gian. "
                    "Kiểm tra server hoặc kết nối mạng."
                )
            except ConnectionError as e:
                print(f"Lỗi kết nối: {e}. Kiểm tra server có đang chạy không.")
                break
            except (EOFError, KeyboardInterrupt):
                print("\nĐã thoát client bằng Ctrl+C.")
                break

    except ConnectionRefusedError:
        print(
            "Không thể kết nối server: Server chưa chạy hoặc sai host/port."
        )
    except TimeoutError:
        print(
            "Kết nối server bị timeout. Kiểm tra địa chỉ và cổng server."
        )
    except ConnectionError as e:
        print(f"Lỗi kết nối: {e}")
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()