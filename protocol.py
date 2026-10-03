"""
Tệp: protocol.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên: Bùi Xuân Khánh & Trương Quốc Anh
Mô tả: Đóng khung thông điệp dạng dòng văn bản bằng ký tự xuống dòng \n
"""

MAX_LINE = 64 * 1024  # Giới hạn an toàn chống cạn RAM (64 KB)


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
