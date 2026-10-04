"""
Tệp: udp_chat_client.py
Môn học: Lập trình mạng - Học kỳ 1 (2026 - 2027)
Nhóm: 05 - Lớp: 24CNTT3
Thành viên thực hiện: Đặng Nhật Thanh (MSSV: 3120224131)
Bài tập: Bài tập thực hành nhóm số 4 - Chương 4 (UDP) - Phần B, mục 1, 2, 3
Mô tả:
  - Mục 1: Đăng nhập có hẹn giờ - gửi lại (dùng ask() trong protocol.py),
           nhập lại tên khi nhận ERR.
  - Mục 2: Luồng nhận chạy nền (daemon) là nơi DUY NHẤT đọc socket sau khi
           đăng nhập: in FROM/SYS, tự gửi PING mỗi 20 giây (nhịp tim).
           Luồng chính đọc bàn phím: nội dung -> cả phòng, @tên nội dung ->
           riêng, /who, /quit; mọi cách thoát đều gửi QUIT.
  - Mục 3: Tìm server trong LAN bằng UDP broadcast (--find): gửi DISCOVER
           tới <broadcast>, gom các phản hồi HERE|... trong 2 giây, kết nối
           tới server đầu tiên tìm được.
Cách chạy:
  python udp_chat_client.py --host 127.0.0.1 --port 9005
  python udp_chat_client.py --find --port 9005
"""

import argparse
import platform
import socket
import sys
import threading
import time

from protocol import ask, send_dgram, recv_dgram, MAX_DGRAM

PING_INTERVAL = 20.0      # giây - chu kỳ nhịp tim theo đặc tả
DISCOVER_WAIT = 2.0       # giây - thời gian gom phản hồi HERE| khi --find


# ==========================================================================
# MỤC 3: TÌM SERVER BẰNG UDP BROADCAST
# ==========================================================================
def in_thong_tin_may_cuc_bo():
    """In thông tin máy đang chạy client - để tiện chụp màn hình điền vào
    bảng 'Máy - Hệ điều hành - IPv4 LAN - Vai trò' của báo cáo (mục 3)."""
    hostname = socket.gethostname()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("8.8.8.8", 80))
            local_ip = probe.getsockname()[0]
        except OSError:
            local_ip = "Không xác định (máy có thể không có mạng)"

    print("-" * 60)
    print("THÔNG TIN MÁY ĐANG CHẠY --find")
    print(f"  Hostname      : {hostname}")
    print(f"  Hệ điều hành  : {platform.system()} {platform.release()}")
    print(f"  Địa chỉ IPv4  : {local_ip}")
    print("-" * 60)


def discover_and_choose_server(port, wait_seconds=DISCOVER_WAIT):
    """
    Bật SO_BROADCAST, gửi DISCOVER tới <broadcast>:port, gom mọi phản hồi
    HERE|... trong `wait_seconds` giây, rồi CHỌN SERVER ĐẦU TIÊN tìm được.
    Trả về (host, port) của server, hoặc None nếu không tìm thấy ai.
    """
    in_thong_tin_may_cuc_bo()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(("", 0))

        print(f"Đang gửi DISCOVER tới <broadcast>:{port}, "
              f"chờ gom phản hồi trong {wait_seconds:.0f} giây...")
        try:
            s.sendto(b"DISCOVER\n", ("<broadcast>", port))
        except OSError as e:
            print(f"Không gửi được gói tin broadcast: {e}")
            return None

        found = []
        deadline = time.monotonic() + wait_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            s.settimeout(remaining)
            try:
                data, addr = s.recvfrom(MAX_DGRAM + 1)
            except socket.timeout:
                break
            line = data.decode("utf-8", errors="replace").strip()
            if line.startswith("HERE|"):
                print(f"  [--find] Tìm thấy server tại {addr}  ->  {line}")
                found.append(addr)

    if not found:
        return None

    print(f"[--find] => Chọn server đầu tiên tìm được: {found[0][0]}:{found[0][1]}")
    return found[0]


# ==========================================================================
# MỤC 1: ĐĂNG NHẬP CÓ HẸN GIỜ - GỬI LẠI, NHẬP LẠI TÊN KHI ERR
# ==========================================================================
def login(sock):
    """Hỏi tên, gửi LOGIN bằng ask() (hẹn giờ/gửi lại), ERR thì cho nhập
    lại; mỗi loại lỗi kết nối/time-out in một câu tiếng Việt rõ ràng."""
    while True:
        try:
            name = input("Nhập tên đăng nhập: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nĐã hủy đăng nhập theo yêu cầu người dùng.")
            return None

        if not name:
            print("Tên không được để trống, vui lòng nhập lại.")
            continue

        try:
            reply = ask(
                sock,
                f"LOGIN|{name}",
                is_match=lambda line: line.startswith("OK|") or line.startswith("ERR|"),
            )
        except ConnectionRefusedError:
            print("Lỗi: Server từ chối kết nối (ConnectionRefusedError) -")
            print("server chưa bật hoặc sai cổng.")
            return None
        except TimeoutError:
            print("Lỗi: Server không phản hồi sau nhiều lần gửi lại (TimeoutError).")
            print("Kiểm tra lại --host/--port hoặc chắc chắn server đang chạy.")
            return None


        if reply.startswith("OK|"):
            print(reply)
            return name

        print(f"Đăng nhập thất bại: {reply}")
        print("Vui lòng nhập một tên khác.")


# ==========================================================================
# MỤC 2: LUỒNG NHẬN CHẠY NỀN (duy nhất đọc socket) + NHỊP TIM
# ==========================================================================
def dinh_dang_thong_diep(line: str):
    """In lại các loại thông điệp server đẩy tới / trả lời cho dễ đọc."""
    if line.startswith("FROM|"):
        # FROM|<nguoi_gui>|<dich>|<noi_dung>
        parts = line.split("|", 3)
        if len(parts) >= 4:
            nguoi_gui, dich, noi_dung = parts[1], parts[2], parts[3]
            nhan = "(riêng)" if dich != "all" else ""
            print(f"\n[{nguoi_gui}]{nhan} {noi_dung}\n> ", end="", flush=True)
        else:
            print(f"\n{line}\n> ", end="", flush=True)
    elif line.startswith("SYS|"):
        print(f"\n[HỆ THỐNG] {line.split('|', 1)[1]}\n> ", end="", flush=True)
    elif line.startswith("PONG|"):
        pass  # phản hồi nhịp tim - không cần làm phiền người dùng
    elif line == "BYE":
        print("\nServer đã xác nhận thoát (BYE).")
    elif line.startswith("OK|") or line.startswith("ERR|"):
        print(f"\n{line}\n> ", end="", flush=True)
    else:
        print(f"\n{line}\n> ", end="", flush=True)


def background_listener(sock, stop_event: threading.Event):
    """
    Luồng nền DUY NHẤT đọc socket sau khi đăng nhập:
      - In ngay các thông điệp FROM/SYS (và các loại khác) nhận được.
      - Tự gửi PING|<n> mỗi PING_INTERVAL giây để giữ nhịp tim, tránh bị
        server dọn vì im lặng quá --idle giây.
      - Bắt OSError (socket đóng, WinError 10054, v.v.) để dừng gọn,
        không làm crash chương trình.
    """
    sock.settimeout(1.0)  # timeout ngắn để định kỳ kiểm tra nhịp tim & stop_event
    ping_id = 0
    last_ping = time.monotonic()

    while not stop_event.is_set():
        now = time.monotonic()
        if now - last_ping >= PING_INTERVAL:
            ping_id += 1
            try:
                send_dgram(sock, f"PING|{ping_id}\n".encode("utf-8"))
            except OSError:
                pass
            last_ping = now

        try:
            reply, _addr, bi_qua_gioi_han = recv_dgram(sock)
        except socket.timeout:
            continue
        except (ConnectionResetError, OSError):
            break  # socket đã đóng hoặc lỗi hệ thống -> dừng luồng nền

        if bi_qua_gioi_han:
            print("\n[CẢNH BÁO] Nhận một datagram có vẻ đã bị cắt bớt "
                  f"(vượt quá {MAX_DGRAM} byte).\n> ", end="", flush=True)
            continue

        line = reply.decode("utf-8", errors="replace").rstrip("\r\n")
        dinh_dang_thong_diep(line)
        if line == "BYE":
            stop_event.set()
            break


# ==========================================================================
# LUỒNG CHÍNH: ĐỌC BÀN PHÍM
# ==========================================================================
def vong_lap_ban_phim(sock, stop_event: threading.Event):
    print("Đã vào phòng chat.")
    print("  - Gõ nội dung                 -> gửi cho cả phòng")
    print("  - Gõ @ten noi_dung             -> gửi riêng cho 'ten'")
    print("  - Gõ /who                      -> xem danh sách người online")
    print("  - Gõ /quit (hoặc Ctrl+C/Ctrl+D) -> thoát phòng\n")

    while not stop_event.is_set():
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nĐã nhận lệnh thoát (Ctrl+C/Ctrl+D), đang gửi QUIT...")
            break

        line = line.strip()
        if not line:
            continue

        if line == "/quit":
            break
        elif line == "/who":
            try:
                send_dgram(sock, b"WHO\n")
            except OSError as e:
                print(f"Lỗi khi gửi /who: {e}")
        elif line.startswith("@"):
            phan_con_lai = line[1:]
            if " " not in phan_con_lai:
                print("Cú pháp sai. Dùng: @ten noi_dung")
                continue
            ten, noi_dung = phan_con_lai.split(" ", 1)
            try:
                send_dgram(sock, f"MSG|{ten}|{noi_dung}\n".encode("utf-8"))
            except ValueError as e:
                print(f"Nội dung quá dài, không gửi được: {e}")
            except OSError as e:
                print(f"Lỗi khi gửi tin riêng: {e}")
        else:
            try:
                send_dgram(sock, f"MSG|all|{line}\n".encode("utf-8"))
            except ValueError as e:
                print(f"Nội dung quá dài, không gửi được: {e}")
            except OSError as e:
                print(f"Lỗi khi gửi tin: {e}")

    # Mọi đường thoát (kể cả /quit, Ctrl+C, Ctrl+D) đều gửi QUIT để giải
    # phóng phiên phía server trước khi đóng chương trình.
    try:
        send_dgram(sock, b"QUIT\n")
    except OSError:
        pass
    stop_event.set()


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    parser = argparse.ArgumentParser(description="UDP Chat Client - Nhóm 05")
    parser.add_argument("--host", default="127.0.0.1",
                         help="Địa chỉ server (mặc định: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9005,
                         help="Cổng UDP của server (mặc định: 9005, nhóm 05)")
    parser.add_argument("--find", action="store_true",
                         help="Tự dò tìm server trong mạng LAN bằng UDP broadcast")
    args = parser.parse_args()

    if args.find:
        server_addr = discover_and_choose_server(args.port)
        if server_addr is None:
            print(f"Không tìm thấy server nào trả lời broadcast trong "
                  f"{DISCOVER_WAIT:.0f} giây.")
            sys.exit(1)
    else:
        server_addr = (args.host, args.port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect() không bắt tay mạng thật; chỉ gán sẵn địa chỉ đích để
        # có thể dùng send()/recv() thay vì sendto()/recvfrom() mỗi lần.
        sock.connect(server_addr)
    except OSError as e:
        print(f"Không thể thiết lập socket tới {server_addr}: {e}")
        sys.exit(1)

    print("=== UDP CHAT CLIENT - NHÓM 05 ===")
    print(f"Server: {server_addr[0]}:{server_addr[1]}")

    username = login(sock)
    if username is None:
        sock.close()
        sys.exit(1)

    stop_event = threading.Event()
    t = threading.Thread(target=background_listener, args=(sock, stop_event), daemon=True)
    t.start()

    try:
        vong_lap_ban_phim(sock, stop_event)
    finally:
        stop_event.set()
        time.sleep(0.3)  # chờ chút để luồng nền kịp in nốt BYE nếu nhận được
        sock.close()
        print("Đã thoát chương trình.")


if __name__ == "__main__":
    main()
