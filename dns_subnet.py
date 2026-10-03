import socket, ipaddress
 
domain = "ued.udn.vn"      # thay bằng tên miền nhóm chọn
print(domain, "->", socket.gethostbyname(domain))
 
iface = ipaddress.ip_interface("192.168.2.43/24")  # IP/mask máy bạn
net = iface.network
print("Mạng:", net.network_address)
print("Broadcast:", net.broadcast_address)
print("Số host:", net.num_addresses - 2)
