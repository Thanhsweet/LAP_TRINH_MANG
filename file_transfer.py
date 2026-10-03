"""
Tệp: file_transfer.py
Sinh viên thực hiện: Trương Quốc Anh
Mô tả: Chương trình truyền tệp nhị phân tin cậy qua socket TCP 
       sử dụng đóng khung tiền tố độ dài 4 byte, hỗ trợ tên tiếng Việt có dấu,
       chống Path Traversal và kiểm tra tính toàn vẹn bằng SHA-256.
"""

import argparse
import hashlib
import json
import os
import socket
from protocol import recv_msg, send_msg


def compute_sha256(filepath: str) -> str:
    """Tính mã băm SHA-256 của một tệp tin bằng cách đọc từng khối 64KB."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_receiver(port: int, save_dir: str = "received_files"):
    """Phía Nhận (Server truyền tệp)"""
    os.makedirs(save_dir, exist_ok=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", port))
        srv.listen(1)
        print(f"[*] Phía nhận đang lắng nghe tại cổng {port}...")
        print(f"[*] Tệp sẽ được lưu vào thư mục: {os.path.abspath(save_dir)}")

        conn, addr = srv.accept()
        with conn:
            print(f"[+] Đã kết nối với: {addr}")

            # 1. Nhận Metadata (Tên tệp tiếng Việt, kích thước)
            meta_bytes = recv_msg(conn)
            if not meta_bytes:
                print("[-] Không nhận được thông tin tệp.")
                return

            metadata = json.loads(meta_bytes.decode("utf-8"))
            raw_filename = metadata["filename"]
            expected_size = metadata["filesize"]

            # BẢO MẬT: Bắt buộc dùng os.path.basename() để chống tấn công Path Traversal
            safe_filename = os.path.basename(raw_filename)
            save_path = os.path.join(save_dir, safe_filename)

            print(f"[+] Đang nhận tệp: '{safe_filename}' ({expected_size:,} byte)...")

            # 2. Nhận toàn bộ khối dữ liệu nhị phân của tệp
            file_data = recv_msg(conn)
            with open(save_path, "wb") as f:
                f.write(file_data)

            # 3. Tính toán đối soát kích thước và mã băm SHA-256
            actual_size = os.path.getsize(save_path)
            sha256_hash = compute_sha256(save_path)

            print("\n" + "=" * 50)
            print("KẾT QUẢ PHÍA NHẬN:")
            print(f"- Tên tệp lưu      : {safe_filename}")
            print(f"- Kích thước thực tế: {actual_size:,} byte")
            print(f"- SHA-256 đầy đủ   : {sha256_hash}")
            print(f"- 8 ký tự đầu      : {sha256_hash[:8].upper()}")
            print("=" * 50)


def run_sender(host: str, port: int, filepath: str):
    """Phía Gửi (Client truyền tệp)"""
    if not os.path.exists(filepath):
        print(f"[-] Lỗi: Không tìm thấy tệp tin '{filepath}'")
        return

    filesize = os.path.getsize(filepath)
    raw_filename = os.path.basename(filepath)
    sha256_hash = compute_sha256(filepath)

    print("=" * 50)
    print("THÔNG TIN PHÍA GỬI:")
    print(f"- Tên tệp gửi      : {raw_filename}")
    print(f"- Kích thước       : {filesize:,} byte")
    print(f"- SHA-256 gốc      : {sha256_hash}")
    print(f"- 8 ký tự đầu      : {sha256_hash[:8].upper()}")
    print("=" * 50)

    with socket.create_connection((host, port), timeout=10.0) as sock:
        print(f"[*] Đã kết nối tới {host}:{port}, đang gửi dữ liệu...")

        # 1. Gửi Metadata dạng JSON đóng gói bằng UTF-8 để giữ nguyên dấu tiếng Việt
        metadata = {"filename": raw_filename, "filesize": filesize}
        send_msg(sock, json.dumps(metadata, ensure_ascii=False).encode("utf-8"))

        # 2. Đọc và gửi toàn bộ dữ liệu nhị phân
        with open(filepath, "rb") as f:
            file_data = f.read()
        send_msg(sock, file_data)

        print("[+] Đã gửi thành công toàn bộ tệp!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chương trình truyền tệp - Trương Quốc Anh")
    parser.add_argument("--mode", choices=["send", "recv"], required=True, help="Chế độ (send hoặc recv)")
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ host gửi tới")
    parser.add_argument("--port", type=int, default=9008, help="Cổng mạng")
    parser.add_argument("--file", help="Đường dẫn tệp gửi (bắt buộc khi mode=send)")
    args = parser.parse_args()

    if args.mode == "recv":
        run_receiver(args.port)
    elif args.mode == "send":
        if not args.file:
            print("[-] Cần cung cấp đường dẫn tệp với tham số --file")
        else:
            run_sender(args.host, args.port, args.file)