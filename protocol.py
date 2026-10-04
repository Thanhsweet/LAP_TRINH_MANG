"""
Tệp: protocol.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên: Bùi Xuân Khánh & Trương Quốc Anh (MAX_DGRAM, send_dgram, recv_dgram
            - khung cơ bản, Khánh sẽ tinh chỉnh thêm cho đúng đặc tả Phần A)
            Đặng Nhật Thanh (hàm ask() - Bài tập 4, Phần B mục 1)
Mô tả: Bài tập 2-3: đóng khung thông điệp TCP dạng dòng văn bản bằng '\n'.
       Bài tập 4  : đóng khung datagram UDP + cơ chế hẹn giờ/gửi lại ask().
"""

import socket
import time

MAX_LINE = 64 * 1024  # Giới hạn an toàn chống cạn RAM (64 KB) - dùng cho TCP


def send_msg(sock, data: bytes):
    """Gửi dữ liệu nhị phân với tiền tố độ dài 4 byte big-endian."""
    sock.sendall(len(data).to_bytes(4, "big") + data)


def _recv_exact(sock, size: int):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(min(65536, size - len(data)))
        if not chunk:
            if not data:
                return None
            raise EOFError("Socket đóng khi chưa nhận đủ thông điệp")
        data.extend(chunk)
    return bytes(data)


def recv_msg(sock):
    """Nhận một khung nhị phân; trả về None nếu EOF trước tiền tố."""
    header = _recv_exact(sock, 4)
    if header is None:
        return None
    size = int.from_bytes(header, "big")
    data = _recv_exact(sock, size)
    if data is None:
        raise EOFError("Socket đóng trước khi nhận nội dung thông điệp")
    return data


def send_line(sock, text: str):
    """Gửi thông điệp kèm ranh giới \\n, mã hóa UTF-8."""
    sock.sendall((text + "\n").encode("utf-8"))


def recv_line(sock, buf=b""):
    """
    Đọc từ socket cho tới khi bắt gặp b'\\n'.
    Trả về tuple: (dòng_nhận_được, bộ_đệm_dư_thừa).
    Nếu socket bị đóng, trả về (None, buf).
    """
    while b"\n" not in buf:
        if len(buf) > MAX_LINE:
            raise ValueError("Dòng vượt quá độ dài tối đa cho phép (MAX_LINE)")
        chunk = sock.recv(4096)
        if not chunk:
            return None, buf
        buf += chunk

    line, _, rest = buf.partition(b"\n")
    # Cắt bỏ ký tự \r của Windows để lấy nội dung thuần
    clean_line = line.decode("utf-8").rstrip("\r")
    return clean_line, rest


# ==============================================================================
# PHẦN BỔ SUNG CHO BÀI TẬP 4 - UDP
# ==============================================================================

MAX_DGRAM = 1200  # Kích thước datagram tối đa theo đặc tả giao thức chat UDP


def send_dgram(sock, data: bytes, addr=None):
    """
    Gửi một datagram, CHẶN (raise ValueError) nếu vượt quá MAX_DGRAM byte -
    đúng yêu cầu "datagram <= 1200 byte" của đặc tả.
    - addr=None       : dùng cho socket ĐÃ connect() tới server -> sock.send()
    - addr=(ip, port) : dùng cho socket CHƯA connect() (ví dụ server phục vụ
                         nhiều client) -> sock.sendto(data, addr)
    """
    if len(data) > MAX_DGRAM:
        raise ValueError(f"Datagram vượt quá {MAX_DGRAM} byte ({len(data)} byte)")
    if addr is None:
        sock.send(data)
    else:
        sock.sendto(data, addr)


def recv_dgram(sock):
    """
    Nhận một datagram, cố tình đọc DƯ 1 byte (MAX_DGRAM + 1) để phát hiện
    trường hợp datagram gốc (do bên gửi cố tình hoặc do lỗi) lớn hơn giới
    hạn cho phép - UDP không bao giờ "cắt rồi gộp lại" như TCP, nên một khi
    nhận đủ MAX_DGRAM + 1 byte, chắc chắn datagram gốc đã vượt giới hạn.
    Trả về (data, addr, bi_qua_gioi_han).
    """
    data, addr = sock.recvfrom(MAX_DGRAM + 1)
    bi_qua_gioi_han = len(data) > MAX_DGRAM
    return data, addr, bi_qua_gioi_han


def ask(sock, msg: str, is_match=None, first_timeout: float = 0.5, max_tries: int = 4):
    """
    Cơ chế HẸN GIỜ - GỬI LẠI CÓ GIỚI HẠN cho giao thức chat trên UDP
    (dùng cho udp_chat_client.py, ví dụ bước đăng nhập LOGIN).

    Giả định `sock` là UDP socket ĐÃ connect() sẵn tới địa chỉ server, nên
    dùng send_dgram(sock, data) / recv_dgram(sock) không cần truyền addr.

    Hành vi:
      - Gửi `msg` (tự thêm ký tự xuống dòng '\\n', mã hóa UTF-8).
      - Chờ `first_timeout` giây (mặc định 0.5s) để nhận phản hồi.
      - Nếu hết giờ mà chưa có phản hồi KHỚP yêu cầu -> GỬI LẠI, thời gian
        chờ của lượt kế tiếp TĂNG GẤP ĐÔI (0.5 -> 1 -> 2 -> 4 giây).
      - Tổng cộng gửi tối đa `max_tries` lần (mặc định 4 lần).
      - `is_match(line)`: hàm nhận một dòng phản hồi (str, đã bỏ '\\n') và
        trả về True/False để LỌC đúng loại phản hồi đang chờ. Mặc định
        (None) chấp nhận bất kỳ dòng nào. Dùng tham số này để bỏ qua các
        datagram KHÔNG liên quan xen vào đúng lúc đang chờ (ví dụ nhận được
        FROM|.../SYS|... trong khi đang chờ OK|/ERR| của LOGIN).

    Trả về: dòng phản hồi hợp lệ (str).
    Raise  : TimeoutError nếu đã gửi đủ `max_tries` lần mà không có phản hồi
             khớp yêu cầu; ConnectionRefusedError nếu hệ điều hành báo cổng
             đích không có dịch vụ lắng nghe.
    """
    if is_match is None:
        is_match = lambda _line: True  # noqa: E731 - hàm lọc mặc định: nhận mọi dòng

    data = (msg + "\n").encode("utf-8")
    timeout = first_timeout
    old_timeout = sock.gettimeout()
    try:
        for attempt in range(1, max_tries + 1):
            send_dgram(sock, data)

            deadline = time.monotonic() + timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break  # hết giờ lượt này -> thoát vòng trong, sang lượt gửi kế tiếp
                sock.settimeout(remaining)
                try:
                    reply, _addr, _bi_qua_gioi_han = recv_dgram(sock)
                except socket.timeout:
                    break
                except ConnectionRefusedError:
                    raise
                except ConnectionResetError as exc:
                    # Socket UDP trên Windows ánh xạ ICMP "port unreachable"
                    # thành WinError 10054/ConnectionResetError. Đổi sang lỗi
                    # có đúng ý nghĩa để client báo "Server từ chối kết nối".
                    raise ConnectionRefusedError(
                        "Cổng UDP đích không có server lắng nghe"
                    ) from exc
                except OSError as exc:
                    # Một số hệ điều hành/Python trả lỗi cổng đóng dưới dạng
                    # OSError thuần thay vì lớp ConnectionRefusedError.
                    error_code = getattr(exc, "winerror", None) or exc.errno
                    if error_code in {61, 111, 10054, 10061}:
                        raise ConnectionRefusedError(
                            "Cổng UDP đích không có server lắng nghe"
                        ) from exc
                    raise

                line = reply.decode("utf-8", errors="replace").rstrip("\r\n")
                if is_match(line):
                    return line
                # Không khớp yêu cầu hiện tại (vd FROM/SYS xen ngang) -> bỏ
                # qua, tiếp tục chờ trong CÙNG lượt gửi này (không tính thêm
                # lượt gửi mới, không reset thời gian chờ).

            timeout *= 2  # lượt chờ kế tiếp tăng gấp đôi, đúng đặc tả

        raise TimeoutError(
            f"Không nhận được phản hồi hợp lệ sau {max_tries} lần gửi: {msg!r}"
        )
    finally:
        sock.settimeout(old_timeout)
