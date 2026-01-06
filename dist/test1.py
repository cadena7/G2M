import socket
HOST= "192.168.7.2"
PORT=9095

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"ESTADO \n")
    data = s.recv(1024)

print(data)
