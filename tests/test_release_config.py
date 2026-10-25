from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_TEXT = (ROOT / "docker-compose.release.yml").read_text()
SERVICES = yaml.safe_load(COMPOSE_TEXT)["services"]
NETWORKS = yaml.safe_load(COMPOSE_TEXT)["networks"]

def test_private_network_has_no_route_to_the_internet():
    assert NETWORKS["private"]["internal"] is True

def test_only_gateway_and_model_puller_touch_the_internet_facing_network():
    for name, svc in SERVICES.items():
        if name in ("gateway", "model-puller"):
            continue
        assert svc["networks"] == ["private"], f"{name} must only be on the private network"

def test_only_the_gateway_publishes_a_port_and_only_on_localhost():
    for name, svc in SERVICES.items():
        ports = svc.get("ports", [])
        if name == "gateway":
            assert ports and all(str(p).startswith("127.0.0.1:") for p in ports)
        else:
            assert not ports, f"{name} must not publish ports"

def test_api_has_no_owner_database_credentials():
    env = SERVICES["api"]["environment"]
    assert "MIGRATION_DATABASE_URL" not in env
    assert "DB_OWNER_PASSWORD" not in str(env)

def test_api_container_is_hardened():
    api = SERVICES["api"]
    assert api["read_only"] is True
    assert "ALL" in api["cap_drop"]
    assert "no-new-privileges:true" in api["security_opt"]

def test_compose_file_contains_no_default_secrets():
    assert "dev_password" not in COMPOSE_TEXT

def test_env_example_contains_placeholders_only():
    for line in (ROOT / ".env.example").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        assert value == "CHANGE_ME", f"{key} must be a CHANGE_ME placeholder"