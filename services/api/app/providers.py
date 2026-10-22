import os
from typing import Protocol
from urllib.parse import urlparse
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
SYSTEM_PROMPT = "You are a helpful, concise assistant."

# Safety rule: the model must run on THIS computer (no silent cloud)
if urlparse(OLLAMA_URL).hostname not in ("127.0.0.1", "localhost", "::1"):
    raise RuntimeError("OLLAMA_URL must point to this computer")

class ModelProvider(Protocol):
    def chat(self, messages: list[dict], model: str) -> str: ...

class OllamaProvider:
    def chat(self, messages: list[dict], model: str) -> str:
        r = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]

class FakeProvider:
    """For tests: no real AI needed."""
    def chat(self, messages: list[dict], model: str) -> str:
        return "FAKE REPLY to: " + messages[-1]["content"]

def get_provider() -> ModelProvider:
    return OllamaProvider()