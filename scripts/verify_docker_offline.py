"""The API container should NOT reach the internet, but SHOULD reach its database and model server.
Run from the project folder while the release stack is running:
    python scripts\\verify_docker_offline.py"""
import subprocess
import sys

CHECK = """
import socket
def ok(host, port):
    try:
        socket.create_connection((host, port), timeout=3).close()
        return True
    except OSError:
        return False
print("internet", ok("1.1.1.1", 443))
print("database", ok("db", 5432))
print("model", ok("ollama", 11434))
"""

result = subprocess.run(
    ["docker", "compose", "-f", "docker-compose.release.yml", "exec", "-T", "api", "python", "-c", CHECK],
    capture_output=True, text=True,
)
if result.returncode != 0:
    print(result.stderr or result.stdout)
    sys.exit("Could not run the check. Is the release stack running?")

seen = dict(line.split() for line in result.stdout.strip().splitlines())
for key, label in (("internet", "Internet (1.1.1.1:443)"),
                   ("database", "Database (db:5432)"),
                   ("model", "Model server (ollama:11434)")):
    print(f"{label:30} reachable: {'YES' if seen[key] == 'True' else 'NO'}")

if seen["internet"] == "True":
    sys.exit("FAILED: the API container can reach the internet.")
if seen["database"] != "True":
    sys.exit("The API container cannot reach its database, so this check proves nothing yet.")
print("PASSED: no internet from the API container, while its own services still work.")