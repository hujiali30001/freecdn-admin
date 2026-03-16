import socket, sys
host = "134.175.67.168"
for port in [22, 2222]:
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect((host, port))
        print(f"PORT {port} OPEN")
        s.close()
    except Exception as e:
        print(f"PORT {port} CLOSED ({e})")
