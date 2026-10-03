
# ==============================================================================
# THÔNG TIN TỆP MÃ NGUỒN
# Nhóm thực hiện   : Nhóm 05
# Thành viên viết  : Đặng Nhật Thanh (MSSV: 3120224131)
# Bài tập          : Bài tập thực hành nhóm số 2 - Phần C (Công cụ DNS)
# Cách chạy        : python dns_lookup.py <tên_miền>
# Ví dụ
#   1. Tên miền .vn:     python dns_lookup.py ued.udn.vn
#   2. Tên miền IPv6:    python dns_lookup.py www.google.org
#   3. Tên miền lỗi:     python dns_lookup.py lose.abc
# ==============================================================================

import sys
import socket


def get_local_ip():

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except OSError:
            ip = "Không xác định được (máy có thể không có kết nối mạng)"
    return ip


def print_header():
    print("=" * 70)
    print("THÔNG TIN MÁY ĐANG CHẠY CHƯƠNG TRÌNH")
    print("=" * 70)
    hostname = socket.gethostname()
    local_ip = get_local_ip()
    print(f"Tên máy (hostname) : {hostname}")
    print(f"Địa chỉ IP LAN     : {local_ip}")
    print()


def lookup_ipv4(domain):
    print("-" * 70)
    print(f"[1] Địa chỉ IPv4 của '{domain}' (gethostbyname)")
    print("-" * 70)
    try:
        ip = socket.gethostbyname(domain)
        print(f"    IPv4: {ip}")
        return ip
    except socket.gaierror as e:
        print(f"    Lỗi phân giải tên miền (gaierror): {e}")
    except OSError as e:
        print(f"    Lỗi hệ thống (OSError) khác: {e}")
    return None


def lookup_getaddrinfo(domain):
    print("-" * 70)
    print(f"[2] Toàn bộ kết quả getaddrinfo('{domain}', 80, SOCK_STREAM)")
    print("-" * 70)
    results = []
    try:
        infos = socket.getaddrinfo(domain, 80, type=socket.SOCK_STREAM)
        for idx, info in enumerate(infos, start=1):
            family, socktype, proto, canonname, sockaddr = info
            family_name = "AF_INET (IPv4)" if family == socket.AF_INET else (
                "AF_INET6 (IPv6)" if family == socket.AF_INET6 else str(family)
            )
            print(f"    Dòng {idx}: họ địa chỉ = {family_name}, sockaddr = {sockaddr}")
            results.append((family_name, sockaddr))
        if not infos:
            print("    Không có kết quả trả về.")
    except socket.gaierror as e:
        print(f"    Lỗi phân giải tên miền (gaierror): {e}")
    except OSError as e:
        print(f"    Lỗi hệ thống (OSError) khác: {e}")
    return results


def reverse_lookup(ip):
    print("-" * 70)
    print(f"[3] Tra ngược địa chỉ IP '{ip}' về tên (gethostbyaddr)")
    print("-" * 70)
    if ip is None:
        print("    Bỏ qua vì không có địa chỉ IPv4 hợp lệ để tra ngược.")
        return
    try:
        name, aliases, addrs = socket.gethostbyaddr(ip)
        print(f"    Tên chính  : {name}")
        print(f"    Bí danh    : {aliases}")
        print(f"    Địa chỉ IP : {addrs}")
    except socket.herror as e:
        print(f"    Không tra ngược được (herror): {e}")
    except socket.gaierror as e:
        print(f"    Lỗi phân giải tên miền (gaierror): {e}")
    except OSError as e:
        print(f"    Lỗi hệ thống (OSError) khác: {e}")


def main():
    if len(sys.argv) != 2:
        print("Cách dùng: python dns_lookup.py <tên_miền>")
        sys.exit(1)

    domain = sys.argv[1]

    print_header()

    print(f"Đang tra cứu thông tin DNS cho tên miền: {domain}")
    print()

    ipv4 = lookup_ipv4(domain)
    print()

    lookup_getaddrinfo(domain)
    print()

    reverse_lookup(ipv4)
    print()

    print("=" * 70)
    print("HOÀN TẤT TRA CỨU")
    print("=" * 70)


if __name__ == "__main__":
    main()