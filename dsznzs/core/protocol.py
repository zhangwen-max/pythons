from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class ChatRequest:
    user_input: str
    session_id: str = "demo-session"
    user_id: str = "demo-user"
    message_id: str = field(default_factory=lambda: f"m-{uuid4().hex[:12]}")
    trace_id: str = field(default_factory=lambda: f"t-{uuid4().hex[:12]}")


@dataclass
class ChatResponse:
    answer: str
    intent: str
    confidence: float
    session_id: str
    trace_id: str
    latency_ms: int
    prompt_version: str

