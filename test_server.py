"""
Tệp: test_server.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên thực hiện: Đặng Nhật Thanh
Lệnh chạy: python test_server.py --host 127.0.0.1 --port 9005
Mô tả: Tự động kiểm thử TCP Chat Server với 7 ca kiểm thử và kiểm tra ranh giới thông điệp
"""

import argparse
import socket
from protocol import recv_line


TEST_USERNAME = "ThanhTest05"
TEST_MESSAGE = "Tin nhan kiem thu"


TEST_CASES = [
    {
        "name": "Chặn MSG khi chưa đăng nhập",
        "command": "MSG|all|Xin chao truoc khi LOGIN",
        "expected": ["ERR|3|Phai LOGIN truoc khi thuc hien lenh khac"],
    },
    {
        "name": "Chặn tên đăng nhập rỗng",
        "command": "LOGIN|",
        "expected": ["ERR|1|Ten khong duoc de trong"],
    },
    {
        "name": "Đăng nhập hợp lệ",
        "command": f"LOGIN|{TEST_USERNAME}",
        "expected": [f"OK|Chao {TEST_USERNAME}"],
    },
    {
        "name": "Chặn LOGIN lần hai trong cùng phiên",
        "command": "LOGIN|NguoiDungKhac",
        "expected": ["ERR|3|Ban da dang nhap roi"],
    },
    {
        "name": "Gửi tin nhắn chung hợp lệ",
        "command": f"MSG|all|{TEST_MESSAGE}",
        "expected": ["OK|Da luu tin nhan"],
    },
    {
        "name": "Đọc đúng phản hồi HISTORY nhiều dòng",
        "command": "HISTORY|1",
        "expected": [
            "HISTORY_ACK|1",
            f"{TEST_USERNAME} : {TEST_MESSAGE}",
        ],
    },
    {
        "name": "Thoát",
        "command": "QUIT",
        "expected": ["BYE"],
    },
]


def build_payload() -> bytes:
    """Gộp toàn bộ 7 lệnh thành một khối byte để chỉ gọi sendall() đúng một lần."""
    text = "".join(f"{case['command']}\n" for case in TEST_CASES)
    return text.encode("utf-8")


def recv_expected_lines(sock: socket.socket, buf: bytes, count: int):
    """Đọc chính xác count dòng phản hồi và giữ lại buffer dư cho lần đọc tiếp theo."""
    lines = []
    for _ in range(count):
        line, buf = recv_line(sock, buf)
        if line is None:
            raise ConnectionError("Server đóng kết nối trước khi trả đủ phản hồi.")
        lines.append(line)
    return lines, buf


def run_tests(host: str, port: int) -> bool:
    """Kết nối server, gửi 7 lệnh trong một sendall() và đối chiếu từng kết quả."""
    print("=== TEST SERVER - NHÓM 05 ===")
    print("Server:", host)
    print("Port:", port)
    print("Số ca kiểm thử:", len(TEST_CASES))
    print()

    with socket.create_connection((host, port), timeout=5.0) as sock:
        sock.settimeout(5.0)

        payload = build_payload()
        print(f"[*] Đã kết nối tới {host}:{port}")
        print(
            f"[*] Gộp {len(TEST_CASES)} lệnh thành {len(payload)} byte "
            "và gửi bằng đúng 1 lần sendall()."
        )
        sock.sendall(payload)
        print("[*] Bắt đầu đọc lần lượt phản hồi từ server...\n")

        buf = b""
        passed = 0

        for index, case in enumerate(TEST_CASES, start=1):
            actual, buf = recv_expected_lines(sock, buf, len(case["expected"]))
            is_passed = actual == case["expected"]

            if is_passed:
                passed += 1

            print(f"[{index}] {case['name']}")
            print(f"    Lệnh gửi   : {case['command']}")
            print(f"    Mong đợi   : {' / '.join(case['expected'])}")
            print(f"    Thực tế    : {' / '.join(actual)}")
            print(f"    Kết quả    : {'ĐẠT' if is_passed else 'SAI'}")
            print("-" * 70)

        print()
        print("=== TỔNG KẾT ===")
        print(f"Đạt: {passed}/{len(TEST_CASES)} ca kiểm thử")

        if passed == len(TEST_CASES):
            print("Kết luận: TẤT CẢ CA KIỂM THỬ ĐỀU ĐẠT.")
            return True

        print("Kết luận: CÒN CA KIỂM THỬ SAI, CẦN KIỂM TRA LẠI SERVER.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử TCP Chat Server - Nhóm 05")
    parser.add_argument("--host", default="10.243.59.89", help="Địa chỉ server")
    parser.add_argument("--port", type=int, default=9005, help="Cổng server")
    args = parser.parse_args()

    try:
        ok = run_tests(args.host, args.port)
        raise SystemExit(0 if ok else 1)
    except ConnectionRefusedError:
        print("Không thể kết nối server: Server chưa chạy hoặc sai host/port.")
        raise SystemExit(2)
    except TimeoutError:
        print("Lỗi: Server phản hồi quá thời gian. Kiểm tra server hoặc kết nối mạng.")
        raise SystemExit(3)
    except ConnectionError as e:
        print(f"Lỗi kết nối: {e}")
        raise SystemExit(4)
    except OSError as e:
        print(f"Lỗi socket: {e}")
        raise SystemExit(5)


if __name__ == "__main__":
    main()
