from __future__ import annotations

import re
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from config import MEMORY_WINDOW_SIZE


@dataclass
class SessionFacts:
    order_id: str | None = None
    new_address: str | None = None
    last_intent: str | None = None


@dataclass
class SessionMemory:
    facts: SessionFacts = field(default_factory=SessionFacts)
    messages: list[BaseMessage] = field(default_factory=list)
    summary: str = ""

    def add_user(self, text: str) -> None:
        self.messages.append(HumanMessage(content=text))
        self._extract_facts(text)
        self._trim()

    def add_ai(self, text: str) -> None:
        self.messages.append(AIMessage(content=text))
        self._trim()

    def update_from_slots(self, slots: dict, primary_intent: str) -> None:
        self.facts.last_intent = primary_intent
        if slots.get("order_id"):
            self.facts.order_id = str(slots["order_id"])
        if slots.get("new_address"):
            self.facts.new_address = str(slots["new_address"])

    def to_messages(self) -> list[BaseMessage]:
        context_parts: list[str] = []
        if self.facts.order_id:
            context_parts.append(f"已知订单号：{self.facts.order_id}")
        if self.facts.new_address:
            context_parts.append(f"已知新地址：{self.facts.new_address}")
        if self.facts.last_intent:
            context_parts.append(f"上次意图：{self.facts.last_intent}")
        if self.summary:
            context_parts.append(f"历史摘要：{self.summary}")
        result: list[BaseMessage] = []
        if context_parts:
            result.append(SystemMessage(content="会话上下文：" + "；".join(context_parts)))
        result.extend(self.messages[-MEMORY_WINDOW_SIZE * 2 :])
        return result

    def _extract_facts(self, text: str) -> None:
        match = re.search(r"(?:订单|order)[^\dA-Za-z]*([A-Za-z0-9-]+)|\b(\d{3,})\b", text, flags=re.I)
        if match:
            self.facts.order_id = match.group(1) or match.group(2)
        if "地址" in text:
            self.facts.new_address = text

    def _trim(self) -> None:
        max_len = MEMORY_WINDOW_SIZE * 2
        if len(self.messages) <= max_len:
            return
        overflow = self.messages[:-max_len]
        brief = " / ".join(str(m.content)[:40] for m in overflow[-4:])
        if brief:
            self.summary = (self.summary + " " + brief).strip()[-500:]
        self.messages = self.messages[-max_len:]


class MemoryManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionMemory] = {}

    def get(self, session_id: str) -> SessionMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory()
        return self._sessions[session_id]

