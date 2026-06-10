from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.prompts import ChatPromptTemplate


SUPPORTED_INTENTS = [
    "track_shipping",
    "change_address",
    "return_refund",
    "complaint",
    "product_consult",
    "general",
]


@dataclass
class IntentResult:
    intents: list[str]
    slots: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reason: str = ""

    @property
    def primary(self) -> str:
        return self.intents[0] if self.intents else "general"


class IntentRecognizer:
    """Use an LLM for intent recognition, with a deterministic fallback."""

    def __init__(self, llm) -> None:
        self._llm = llm
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是电商客服意图识别器。只输出 JSON，不要输出解释文字。"
                    "可选 intent: track_shipping, change_address, return_refund, "
                    "complaint, product_consult, general。"
                    "输出格式: {{\"intent\":[\"...\"],\"slots\":{{}},\"confidence\":0.0,\"reason\":\"...\"}}",
                ),
                (
                    "human",
                    "用户输入：{user_input}\n"
                    "要求：支持多意图；抽取 order_id、new_address、product_name 等槽位。",
                ),
            ]
        )

    def recognize(self, user_input: str) -> IntentResult:
        try:
            raw = (self._prompt | self._llm).invoke({"user_input": user_input}).content
            data = self._parse_json(raw)
            intents = [x for x in data.get("intent", []) if x in SUPPORTED_INTENTS]
            if not intents:
                intents = ["general"]
            return IntentResult(
                intents=intents,
                slots=data.get("slots", {}) or {},
                confidence=float(data.get("confidence", 0.0)),
                reason=str(data.get("reason", "")),
            )
        except Exception:
            return self._rule_fallback(user_input)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            text = match.group(0)
        return json.loads(text)

    @staticmethod
    def _rule_fallback(user_input: str) -> IntentResult:
        text = user_input.lower()
        intents: list[str] = []
        slots: dict[str, Any] = {}
        order_match = re.search(r"(?:订单|order)[^\dA-Za-z]*([A-Za-z0-9-]+)|\b(\d{3,})\b", user_input)
        if order_match:
            slots["order_id"] = order_match.group(1) or order_match.group(2)
        if any(k in text for k in ["物流", "快递", "到哪", "签收"]):
            intents.append("track_shipping")
        if any(k in text for k in ["改地址", "换地址", "修改地址", "新地址"]):
            intents.append("change_address")
        if any(k in text for k in ["退货", "退款", "退换"]):
            intents.append("return_refund")
        if any(k in text for k in ["投诉", "差评", "生气", "不满"]):
            intents.append("complaint")
        if any(k in text for k in ["推荐", "买", "商品", "尺码", "库存", "优惠"]):
            intents.append("product_consult")
        if not intents:
            intents.append("general")
        return IntentResult(intents=intents, slots=slots, confidence=0.72, reason="rule_fallback")
