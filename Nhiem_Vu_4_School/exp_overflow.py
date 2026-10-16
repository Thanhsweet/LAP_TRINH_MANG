"""
Tệp: exp_overflow.py
Nhóm: 05
Thành viên thực hiện đo đạc: Trần Quốc Trường
Lệnh chạy: 
    python exp_overflow.py
Nguồn: Mã nguồn lấy từ slide bài giảng Chương 4 (mục 4.4).
"""

import socket
import time
import threading
import platform

HOST = '127.0.0.1'
PORT = 9999
NUM_MSGS = 100000  # Đẩy số lượng gói lên cao để ép tràn bộ đệm

def receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    
    # Lấy thông số hệ điều hành và kích thước bộ đệm nhận UDP mặc định
    os_name = platform.system() + " " + platform.release()
    buf_size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    
    print("=== THÔNG SỐ HỆ THỐNG ===")
    print(f"Hệ điều hành               : {os_name}")
    print(f"Giá trị SO_RCVBUF mặc định : {buf_size} bytes")
    print("=========================\n")
    
    received_count = 0
    # Đặt timeout ngắn để kết thúc quá trình đếm khi client ngừng xả gói
    sock.settimeout(2.0)
    
    print(f"[*] Server đang chờ nhận {NUM_MSGS} gói tin...")
    try:
        while True:
            data, _ = sock.recvfrom(1024)
            received_count += 1
    except socket.timeout:
        pass
        
    loss_rate = ((NUM_MSGS - received_count) / NUM_MSGS) * 100
    print("\n=== KẾT QUẢ ĐO ĐẠC TRÀN BỘ ĐỆM (BẢNG 5) ===")
    print(f"Số gói tin gửi đi      : {NUM_MSGS}")
    print(f"Số gói tin nhận được   : {received_count}")
    print(f"Số gói tin bị mất      : {NUM_MSGS - received_count}")
    print(f"Tỉ lệ mất gói (Loss)   : {loss_rate:.2f}%")
    sock.close()

def sender():
    time.sleep(0.5)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[*] Client bắt đầu xả nhanh {NUM_MSGS} gói tin...")
    
    # Gửi liên tục không có độ trễ để gây nghẽn bộ đệm nhận
    payload = b"X" * 100
    for _ in range(NUM_MSGS):
        sock.sendto(payload, (HOST, PORT))
        
    print("[*] Client đã xả xong dữ liệu.")
    sock.close()

if __name__ == "__main__":
    t_recv = threading.Thread(target=receiver)
    t_send = threading.Thread(target=sender)
    
    t_recv.start()
    t_send.start()
    
    t_recv.join()
    t_send.join()