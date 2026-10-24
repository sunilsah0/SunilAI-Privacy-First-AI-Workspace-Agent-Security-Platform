import ipaddress
import os
import socket

OFFLINE_MODE = os.getenv("OFFLINE_MODE", "1") == "1"   # strict offline is the default

_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_installed = False

def is_local_host(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.split("%")[0]).is_loopback
    except ValueError:
        return False   # a hostname such as example.com: not allowed

def _check(address) -> None:
    if isinstance(address, tuple) and address:
        host = str(address[0])
        if not is_local_host(host):
            raise PermissionError(f"Blocked outbound connection to {host} (offline mode)")

def install_guard() -> None:
    """Replace socket.connect so external addresses are refused BEFORE any packet is sent."""
    global _installed
    if _installed:
        return

    def guarded_connect(self, address):
        _check(address)
        return _original_connect(self, address)

    def guarded_connect_ex(self, address):
        _check(address)
        return _original_connect_ex(self, address)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    _installed = True

def is_installed() -> bool:
    return _installed

def raw_probe(host: str = "1.1.1.1", port: int = 443, timeout: float = 3.0) -> bool:
    """Bypasses the guard ON PURPOSE, so we test the operating-system layer.
    Only used when the user explicitly asks for it."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return _original_connect_ex(s, (host, port)) == 0
    except OSError:
        return False
    finally:
        s.close()