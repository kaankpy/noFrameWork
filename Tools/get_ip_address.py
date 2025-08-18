import socket

def get_ip_address():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "Unavailable"

if __name__ == "__main__":
    print("IP Address:", get_ip_address())