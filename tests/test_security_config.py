import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_KEYS = ("SECRET_KEY", "APP_ENV", "REGISTRATION_MODE", "INVITE_CODE", "EDITION", "DEMO_MODE")


def run_import(**env_changes):
    env = {k: v for k, v in os.environ.items() if k not in CONFIG_KEYS}
    env.update(env_changes)
    return subprocess.run([sys.executable, "-c", "import services.api.app.security"],
                          cwd=ROOT, capture_output=True, text=True, env=env)


def test_production_requires_a_strong_secret_key():
    missing = run_import(APP_ENV="production")
    assert missing.returncode != 0 and "SECRET_KEY" in missing.stderr
    too_short = run_import(APP_ENV="production", SECRET_KEY="short")
    assert too_short.returncode != 0 and "SECRET_KEY" in too_short.stderr
    good = run_import(APP_ENV="production", SECRET_KEY="a" * 64,
                      REGISTRATION_MODE="closed", EDITION="personal")
    assert good.returncode == 0


def test_configuration_is_validated_at_startup():
    key = "a" * 64
    assert run_import().returncode == 0                                       # development defaults
    bad_mode = run_import(REGISTRATION_MODE="whenever")
    assert bad_mode.returncode != 0 and "REGISTRATION_MODE" in bad_mode.stderr
    weak_code = run_import(REGISTRATION_MODE="invite", INVITE_CODE="short")
    assert weak_code.returncode != 0 and "INVITE_CODE" in weak_code.stderr
    bad_edition = run_import(EDITION="galaxy")
    assert bad_edition.returncode != 0 and "EDITION" in bad_edition.stderr
    unset = run_import(APP_ENV="production", SECRET_KEY=key)                  # production must choose
    assert unset.returncode != 0
