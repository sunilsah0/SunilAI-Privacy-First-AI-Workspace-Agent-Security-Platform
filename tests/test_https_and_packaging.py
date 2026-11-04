import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = yaml.safe_load((ROOT / "docker-compose.https.yml").read_text())
CADDYFILE = (ROOT / "deployment" / "containers" / "Caddyfile").read_text()
WIPE = (ROOT / "scripts" / "wipe_demo.sh").read_text()
INSTALL_PS1 = (ROOT / "scripts" / "packaging" / "install.ps1").read_text()
INSTALL_SH = (ROOT / "scripts" / "packaging" / "install.sh").read_text()


def test_only_caddy_publishes_ports_and_only_80_and_443():
    assert OVERLAY["services"]["caddy"]["ports"] == ["80:80", "443:443"]
    for name, svc in OVERLAY["services"].items():
        if name != "caddy":
            assert not svc.get("ports"), f"{name} must not publish ports"


def test_caddy_joins_both_networks_and_the_plain_gateway_is_switched_off():
    assert OVERLAY["services"]["caddy"]["networks"] == ["private", "edge"]
    assert OVERLAY["services"]["gateway"]["profiles"] == ["http-only"]


def test_https_settings_are_required_not_defaulted():
    env = OVERLAY["services"]["caddy"]["environment"]
    assert ":?" in env["SITE_ADDRESS"]
    assert ":?" in env["ACME_EMAIL"]


def test_caddyfile_sets_security_headers_and_proxies_only_the_api():
    for needle in ("Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options",
                   "handle_path /api/*", "reverse_proxy api:8000", "max_size"):
        assert needle in CADDYFILE, needle


def test_wipe_script_refuses_to_run_outside_demo_mode():
    assert "DEMO_MODE=1" in WIPE
    assert WIPE.index("DEMO_MODE=1") < WIPE.index("TRUNCATE")
    assert "exit 1" in WIPE[: WIPE.index("TRUNCATE")]


def test_installers_keep_existing_settings_and_write_plain_text():
    assert "already exists" in INSTALL_PS1 and "already exists" in INSTALL_SH
    assert "-Encoding ascii" in INSTALL_PS1


def test_installers_use_a_cryptographic_random_source():
    assert "RandomNumberGenerator" in INSTALL_PS1 and "Get-Random" not in INSTALL_PS1
    assert "/dev/urandom" in INSTALL_SH


def test_packages_contain_what_people_need(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    subprocess.run([sys.executable, "scripts/make_packages.py", "vtest", str(tmp_path)], cwd=ROOT, check=True)
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "SHA256SUMS.txt", "SunilAI-enterprise-vtest.zip", "SunilAI-personal-vtest.zip"]
    for edition, mode in (("personal", "first_user"), ("enterprise", "invite")):
        prefix = f"SunilAI-{edition}-vtest/"
        with zipfile.ZipFile(tmp_path / f"SunilAI-{edition}-vtest.zip") as z:
            members = z.namelist()
            for needed in ("install.ps1", "install.sh", "README-FIRST.md", "docker-compose.release.yml"):
                assert prefix + needed in members, needed
            assert not any(m.startswith((prefix + "tests/", prefix + ".github/")) for m in members)
            assert prefix + ".env" not in members          # no secrets are shipped
            template = z.read(prefix + ".env.template").decode()
            assert f"EDITION={edition}" in template and f"REGISTRATION_MODE={mode}" in template
