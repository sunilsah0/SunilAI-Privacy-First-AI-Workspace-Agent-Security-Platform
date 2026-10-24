from dataclasses import dataclass
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

# Phase 7 turns this into a real setting enforced by the operating system.
# For now it is only a flag, so treat it as "configured, not yet enforced".
#NETWORK_ALLOWED = False
from .network_guard import OFFLINE_MODE

# Network tools are blocked by policy whenever strict offline mode is on.
NETWORK_ALLOWED = not OFFLINE_MODE
class NoExtra(BaseModel):
    model_config = ConfigDict(extra="forbid")   # unknown arguments are rejected

class SearchArgs(NoExtra):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=4, ge=1, le=20)

class DocArgs(NoExtra):
    document_id: UUID

class SendArgs(NoExtra):
    to: str = Field(max_length=200)
    body: str = Field(max_length=5000)

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    enabled_by_default: bool
    requires_approval: bool
    needs_network: bool

REGISTRY = {t.name: t for t in [
    ToolSpec("search_documents", 'search_documents {"query": str, "k": int}: search my documents',
             SearchArgs, True, False, False),
    ToolSpec("read_document", 'read_document {"document_id": uuid}: read one of my documents',
             DocArgs, True, False, False),
    ToolSpec("delete_document", 'delete_document {"document_id": uuid}: delete one of my documents',
             DocArgs, False, True, False),
    ToolSpec("send_external_message", 'send_external_message {"to": str, "body": str}: send data outside this computer',
             SendArgs, False, True, True),
]}

@dataclass
class Decision:
    outcome: str   # "allow" | "needs_approval" | "deny"
    reason: str

def decide(tool_name: str, granted: dict[str, bool], network_allowed: bool) -> Decision:
    """Plain code. No AI involved. The model's words never change this result."""
    spec = REGISTRY.get(tool_name)
    if spec is None:
        return Decision("deny", "Unknown tool")
    if spec.needs_network and not network_allowed:
        return Decision("deny", "Network access is turned off (offline mode)")
    if not granted.get(tool_name, spec.enabled_by_default):
        return Decision("deny", f"Tool '{tool_name}' is not enabled. You can enable it in permissions.")
    if spec.requires_approval:
        return Decision("needs_approval", "This action needs your approval")
    return Decision("allow", "Allowed")