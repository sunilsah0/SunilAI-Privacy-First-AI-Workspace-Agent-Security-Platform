"""Can THIS Python reach the internet? Can it reach the local database?
Run:  python scripts\\check_network.py"""
import socket

def can_connect(host, port, timeout=3):
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except OSError:
        return False

internet = can_connect("1.1.1.1", 443)
local_db = can_connect("127.0.0.1", 5433)
print(f"Internet (1.1.1.1:443) reachable from Python: {'YES' if internet else 'NO'}")
print(f"Local database (127.0.0.1:5433) reachable:     {'YES' if local_db else 'NO'}")