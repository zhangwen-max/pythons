from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from config import TRACE_ENABLED


@dataclass
class TraceSpan:
    stage: str
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def latency_ms(self) -> int:
        end = self.end_time or time.time()
        return int((end - self.start_time) * 1000)

    def finish(self, **data: Any) -> "TraceSpan":
        self.end_time = time.time()
        self.data.update(data)
        return self


class TraceContext:
    def __init__(self, trace_id: str, session_id: str) -> None:
        self.trace_id = trace_id
        self.session_id = session_id
        self.start_time = time.time()
        self.spans: list[TraceSpan] = []

    def span(self, stage: str) -> TraceSpan:
        span = TraceSpan(stage=stage)
        self.spans.append(span)
        return span

    def emit(self) -> None:
        if not TRACE_ENABLED:
            return
        payload = {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "total_latency_ms": int((time.time() - self.start_time) * 1000),
            "spans": [
                {"stage": s.stage, "latency_ms": s.latency_ms, **s.data}
                for s in self.spans
            ],
        }
        print("[trace] " + json.dumps(payload, ensure_ascii=False))

