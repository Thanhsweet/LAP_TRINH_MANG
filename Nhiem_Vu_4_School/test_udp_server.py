"""
Tệp: test_udp_server.py
Môn: Lập trình mạng - Bài thực hành nhóm số 4
Nhóm: 05

Phần B - Mục 4:
- Tối thiểu 8 ca kiểm thử
- Có ít nhất 3 ca dữ liệu sai
- Có ca LOGIN gửi lại
- Có ca nội dung > 1000 byte
- Có ca gửi trực tiếp datagram 1300 byte bằng sock.send()
- Có timeout + retry
"""

import socket
import time

from protocol import ask, MAX_DGRAM


HOST = "127.0.0.1"
PORT = 9005

FIRST_TIMEOUT = 0.5
MAX_TRIES = 4


# ============================================================
# HÀM HỖ TRỢ
# ============================================================

def tao_socket():
    """Tạo UDP socket và connect tới Server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((HOST, PORT))
    return sock


def ask_test(sock, msg, is_match=None):
    """
    Gửi yêu cầu bằng cơ chế ask():
    0.5 -> 1 -> 2 -> 4 giây
    tối đa 4 lần.
    """
    return ask(
        sock,
        msg,
        is_match=is_match,
        first_timeout=FIRST_TIMEOUT,
        max_tries=MAX_TRIES
    )


def check_response(actual, expected):
    """Kiểm tra phản hồi có đúng kỳ vọng hay không."""
    if actual == expected:
        return True

    print(f"    [SAI] Mong đợi : {expected}")
    print(f"    [SAI] Thực tế  : {actual}")
    return False


def run_test(number, description, function):
    """Chạy một ca kiểm thử và in ĐẠT/SAI."""
    print("\n" + "=" * 70)
    print(f"TC{number:02d}: {description}")
    print("=" * 70)

    try:
        result = function()

        if result:
            print(f"--> TC{number:02d}: ĐẠT")
            return True
        else:
            print(f"--> TC{number:02d}: SAI")
            return False

    except TimeoutError as e:
        print(f"--> TC{number:02d}: SAI - TimeoutError")
        print(f"    {e}")
        return False

    except ConnectionRefusedError as e:
        print(f"--> TC{number:02d}: SAI - ConnectionRefusedError")
        print(f"    {e}")
        return False

    except Exception as e:
        print(f"--> TC{number:02d}: SAI - {type(e).__name__}")
        print(f"    {e}")
        return False


# ============================================================
# TC01 - SAI TRÌNH TỰ
# ============================================================

def tc01():
    """
    Gửi MSG trước LOGIN.
    Server phải trả:
    ERR|3|Chưa đăng nhập
    """
    with tao_socket() as sock:

        reply = ask_test(
            sock,
            "MSG|all|chào",
            is_match=lambda x: x.startswith("ERR|3|")
        )

        print(f"    Server: {reply}")

        return check_response(
            reply,
            "ERR|3|Chưa đăng nhập"
        )


# ============================================================
# TC02 - LOGIN
# ============================================================

def tc02():
    """
    LOGIN với tên hợp lệ.
    """
    with tao_socket() as sock:

        reply = ask_test(
            sock,
            "LOGIN|TestBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        print(f"    Server: {reply}")

        return check_response(
            reply,
            "OK|Chào TestBinh"
        )


# ============================================================
# TC03 - LOGIN GỬI LẠI
# ============================================================

def tc03():
    """
    Gửi LOGIN hai lần trên cùng một socket.

    Server được thiết kế idempotent:
    LOGIN lại cùng tên từ cùng địa chỉ
    phải trả OK|Chào tên.
    """
    with tao_socket() as sock:

        reply1 = ask_test(
            sock,
            "LOGIN|RetryBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        print(f"    Lần 1: {reply1}")

        if reply1 != "OK|Chào RetryBinh":
            return False

        reply2 = ask_test(
            sock,
            "LOGIN|RetryBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        print(f"    Lần 2: {reply2}")

        return check_response(
            reply2,
            "OK|Chào RetryBinh"
        )


# ============================================================
# TC04 - MSG HỢP LỆ
# ============================================================

def tc04():
    """
    LOGIN trước rồi gửi tin nhắn hợp lệ.
    """
    with tao_socket() as sock:

        login_reply = ask_test(
            sock,
            "LOGIN|MsgBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        if login_reply != "OK|Chào MsgBinh":
            print(f"    LOGIN thất bại: {login_reply}")
            return False

        reply = ask_test(
            sock,
            "MSG|all|Xin chao phong",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        print(f"    Server: {reply}")

        return check_response(
            reply,
            "OK|Đã gửi"
        )


# ============================================================
# TC05 - NỘI DUNG QUÁ 1000 BYTE
# ============================================================

def tc05():
    """
    Server quy định MAX_TEXT = 1000 byte.
    Gửi nội dung 1001 byte.
    """
    with tao_socket() as sock:

        login_reply = ask_test(
            sock,
            "LOGIN|LongTextBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        if login_reply != "OK|Chào LongTextBinh":
            print(f"    LOGIN thất bại: {login_reply}")
            return False

        text = "A" * 1001

        reply = ask_test(
            sock,
            f"MSG|all|{text}",
            is_match=lambda x: x.startswith("ERR|4|")
        )

        print(f"    Server: {reply}")

        return check_response(
            reply,
            "ERR|4|Nội dung quá 1000 byte"
        )


# ============================================================
# TC06 - NGƯỜI NHẬN KHÔNG TRỰC TUYẾN
# ============================================================

def tc06():
    """
    Gửi tin riêng tới người không tồn tại.
    """
    with tao_socket() as sock:

        login_reply = ask_test(
            sock,
            "LOGIN|PrivateBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        if login_reply != "OK|Chào PrivateBinh":
            print(f"    LOGIN thất bại: {login_reply}")
            return False

        reply = ask_test(
            sock,
            "MSG|KhongTonTai|Xin chao",
            is_match=lambda x: x.startswith("ERR|5|")
        )

        print(f"    Server: {reply}")

        return check_response(
            reply,
            "ERR|5|Người nhận không trực tuyến"
        )


# ============================================================
# TC07 - WHO
# ============================================================

def tc07():
    """
    LOGIN rồi yêu cầu danh sách người dùng.
    """
    with tao_socket() as sock:

        login_reply = ask_test(
            sock,
            "LOGIN|WhoBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        if login_reply != "OK|Chào WhoBinh":
            print(f"    LOGIN thất bại: {login_reply}")
            return False

        reply = ask_test(
            sock,
            "WHO",
            is_match=lambda x: x.startswith("WHO|")
        )

        print(f"    Server: {reply}")

        if reply.startswith("WHO|") and "WhoBinh" in reply:
            return True

        return False


# ============================================================
# TC08 - DATAGRAM 1300 BYTE
# ============================================================

def tc08():
    """
    BẮT BUỘC dùng sock.send(), không dùng send_dgram().

    MAX_DGRAM = 1200 byte.
    Gửi trực tiếp 1300 byte để kiểm tra Server bỏ qua
    datagram vượt giới hạn mà không dừng.
    """
    with tao_socket() as sock:

        login_reply = ask_test(
            sock,
            "LOGIN|BigPacketBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        if login_reply != "OK|Chào BigPacketBinh":
            print(f"    LOGIN thất bại: {login_reply}")
            return False

        big_packet = b"A" * 1300

        print("    Gửi trực tiếp datagram 1300 byte bằng sock.send()...")
        print(f"    MAX_DGRAM của giao thức: {MAX_DGRAM} byte")

        sent = sock.send(big_packet)

        print(f"    Đã gửi: {sent} byte")
        print("    Server phải bỏ qua datagram này.")

        # Không chờ phản hồi cho gói 1300 byte.
        time.sleep(0.2)

        return sent == 1300


# ============================================================
# TC09 - KIỂM TRA SERVER VẪN HOẠT ĐỘNG SAU DATAGRAM 1300 BYTE
# ============================================================

def tc09():
    """
    Đây là ca bổ sung để chứng minh yêu cầu của TC08:

    Sau khi Server nhận datagram 1300 byte và bỏ qua,
    Server vẫn phải tiếp tục xử lý yêu cầu tiếp theo.
    """
    with tao_socket() as sock:

        login_reply = ask_test(
            sock,
            "LOGIN|AfterBigBinh",
            is_match=lambda x: x.startswith("OK|") or x.startswith("ERR|")
        )

        if login_reply != "OK|Chào AfterBigBinh":
            print(f"    LOGIN thất bại: {login_reply}")
            return False

        big_packet = b"B" * 1300

        print("    Gửi datagram 1300 byte...")
        sock.send(big_packet)

        time.sleep(0.2)

        print("    Gửi WHO để kiểm tra Server còn hoạt động...")

        reply = ask_test(
            sock,
            "WHO",
            is_match=lambda x: x.startswith("WHO|")
        )

        print(f"    Server: {reply}")

        return reply.startswith("WHO|")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("        KIỂM THỬ UDP SERVER - NHÓM 05")
    print("=" * 70)
    print(f"Server: {HOST}:{PORT}")
    print(f"Retry : {FIRST_TIMEOUT} -> 1 -> 2 -> 4 giây")
    print(f"Max tries: {MAX_TRIES}")
    print("=" * 70)

    results = []

    tests = [
        (1, "Sai trình tự - MSG trước LOGIN", tc01),
        (2, "LOGIN hợp lệ", tc02),
        (3, "LOGIN gửi lại", tc03),
        (4, "MSG hợp lệ", tc04),
        (5, "Nội dung MSG quá 1000 byte", tc05),
        (6, "Gửi riêng tới người không trực tuyến", tc06),
        (7, "WHO - xem danh sách người online", tc07),
        (8, "Gửi trực tiếp datagram 1300 byte", tc08),
        (9, "Server vẫn hoạt động sau datagram 1300 byte", tc09),
    ]

    for number, description, function in tests:
        result = run_test(number, description, function)
        results.append((number, result))

        # Nghỉ ngắn giữa các ca
        time.sleep(0.3)

    # ========================================================
    # TỔNG KẾT
    # ========================================================

    print("\n")
    print("=" * 70)
    print("                         TỔNG KẾT")
    print("=" * 70)

    dat = sum(1 for _, result in results if result)
    sai = len(results) - dat

    for number, result in results:
        status = "ĐẠT" if result else "SAI"
        print(f"TC{number:02d}: {status}")

    print("-" * 70)
    print(f"Tổng số ca : {len(results)}")
    print(f"ĐẠT        : {dat}")
    print(f"SAI        : {sai}")
    print("=" * 70)


if __name__ == "__main__":
    main()