import os
import socket
import subprocess
import sys
from pathlib import Path
import pytest
import tests.helpers  # noqa: F401  (importing the app installs the guard)
from services.api.app import network_guard
from services.api.app.policy import NETWORK_ALLOWED, decide

@pytest.fixture(autouse=True)
def guard_on():
    network_guard.install_guard()

def test_guard_blocks_external_ip_before_any_packet():
    with pytest.raises(PermissionError):
        socket.create_connection(("203.0.113.10", 80), timeout=1)   # reserved test address

def test_guard_blocks_hostnames_without_a_dns_lookup():
    s = socket.socket()
    try:
        with pytest.raises(PermissionError):
            s.connect(("example.com", 80))
    finally:
        s.close()

def test_guard_still_allows_loopback():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    try:
        socket.create_connection(("127.0.0.1", port), timeout=2).close()
    finally:
        server.close()

def test_non_local_model_url_is_refused_at_startup():
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [sys.executable, "-c", "import services.api.app.providers"],
        cwd=root, capture_output=True, text=True,
        env={**os.environ, "OLLAMA_URL": "http://example.com:11434"},
    )
    assert r.returncode != 0
    assert "must point to this computer" in r.stderr

def test_offline_mode_turns_network_tools_off():
    assert NETWORK_ALLOWED is False
    d = decide("send_external_message", {"send_external_message": True}, NETWORK_ALLOWED)
    assert d.outcome == "deny"