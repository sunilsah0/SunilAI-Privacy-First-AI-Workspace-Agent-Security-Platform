import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_import(**env_changes):
    env = {k: v for k, v in os.environ.items() if k != "SECRET_KEY"}
    env.update(env_changes)
    return subprocess.run([sys.executable, "-c", "import services.api.app.security"],
                          cwd=ROOT, capture_output=True, text=True, env=env)

def test_production_requires_a_strong_secret_key():
    missing = run_import(APP_ENV="production")
    assert missing.returncode != 0 and "SECRET_KEY" in missing.stderr
    too_short = run_import(APP_ENV="production", SECRET_KEY="short")
    assert too_short.returncode != 0 and "SECRET_KEY" in too_short.stderr
    good = run_import(APP_ENV="production", SECRET_KEY="a" * 64)
    assert good.returncode == 0