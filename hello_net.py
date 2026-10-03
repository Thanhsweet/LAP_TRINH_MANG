import socket
 
host = socket.gethostname()
print("Máy:", host)
for family, _, _, _, addr in socket.getaddrinfo(host, None):
    print(family.name, addr[0])
