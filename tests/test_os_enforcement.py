import os
import pytest
from services.api.app import network_guard

pytestmark = pytest.mark.skipif(
    os.getenv("VERITY_OS_FIREWALL_TEST") != "1",
    reason="Run only after scripts/offline-on.ps1 (set VERITY_OS_FIREWALL_TEST=1)",
)

def test_internet_blocked_by_os_but_local_database_still_works():
    # raw_probe bypasses the in-app guard, so this tests the operating system itself
    assert network_guard.raw_probe("127.0.0.1", 5433), "local database should still work"
    assert not network_guard.raw_probe("1.1.1.1", 443), "internet should be blocked by the OS firewall"