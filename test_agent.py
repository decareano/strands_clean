import socket
import sys


def check_port(host="localhost", port=8000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


if check_port():
    print("✅ Port 8000 is open and accepting connections")
else:
    print("❌ Port 8000 is closed. Your server is not running.")
    print("Start your server with: uvicorn main:app --reload --port 8000")
