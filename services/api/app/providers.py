import os, math, hashlib
from typing import Protocol
from urllib.parse import urlparse
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_DIM = 768  # nomic-embed-text produces 768 numbers per text
SYSTEM_PROMPT = "You are a helpful, concise assistant."

# Safety rule: models must run on THIS computer (no silent cloud)
# Safety rule: the model must run on THIS computer, or on a host we explicitly list
_extra_hosts = {h.strip() for h in os.getenv("ALLOWED_MODEL_HOSTS", "").split(",") if h.strip()}
if urlparse(OLLAMA_URL).hostname not in ({"127.0.0.1", "localhost", "::1"} | _extra_hosts):
    raise RuntimeError("OLLAMA_URL must point to this computer (or a host listed in ALLOWED_MODEL_HOSTS)")
class ModelProvider(Protocol):
    def chat(self, messages: list[dict], model: str) -> str: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...

class OllamaProvider:
    def chat(self, messages: list[dict], model: str) -> str:
        r = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        r = httpx.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["embeddings"]

def _fake_vector(text: str) -> list[float]:
    v = [0.0] * EMBED_DIM
    for word in text.lower().split():
        i = int(hashlib.md5(word.encode()).hexdigest(), 16) % EMBED_DIM
        v[i] += 1.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]

class FakeProvider:
    """For tests: no real AI needed."""
    def chat(self, messages: list[dict], model: str) -> str:
        return "Demo reply (no real AI is running): " + messages[-1]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_fake_vector(t) for t in texts]

#def get_provider() -> ModelProvider:
    #return OllamaProvider()

def get_provider() -> ModelProvider:
    if os.getenv("MODEL_PROVIDER", "ollama") == "fake":
       return FakeProvider()          # demo servers: simulated replies, no real AI
    return OllamaProvider()