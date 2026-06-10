from __future__ import annotations

import time
from collections.abc import Generator

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from config import (
    API_KEY,
    API_KEY_ENV,
    CHAT_TEMPERATURE,
    INTENT_TEMPERATURE,
    MODEL_NAME,
    OPENAI_BASE_URL,
    PROMPT_VERSION,
)
from core.intent import IntentRecognizer
from core.memory import MemoryManager
from core.protocol import ChatRequest, ChatResponse
from core.router import IntentRouter
from core.security import InputGuard, OutputAuditor
from core.tools import execute_business_tool
from core.trace import TraceContext


class ChatService:
    """Ecommerce assistant pipeline: guard -> intent -> route -> tool -> LLM -> memory."""

    def __init__(self) -> None:
        if not API_KEY:
            raise RuntimeError(f"{API_KEY_ENV} 未配置，请在环境变量或 .env 中设置")
        self._intent_llm = ChatOpenAI(
            model=MODEL_NAME,
            api_key=API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=INTENT_TEMPERATURE,
        )
        self._chat_llm = ChatOpenAI(
            model=MODEL_NAME,
            api_key=API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=CHAT_TEMPERATURE,
        )
        self._intent = IntentRecognizer(self._intent_llm)
        self._router = IntentRouter()
        self._memory = MemoryManager()
        self._input_guard = InputGuard()
        self._output_auditor = OutputAuditor()

    def handle(self, req: ChatRequest) -> ChatResponse:
        start = time.time()
        trace = TraceContext(req.trace_id, req.session_id)
        trace.span("receive").finish(user_input=req.user_input[:100])

        guard = self._input_guard.check(req.user_input)
        trace.span("input_guard").finish(is_safe=guard.is_safe, risk=guard.risk_level)
        if not guard.is_safe:
            return self._response(req, "输入包含高风险指令，已拒绝处理。", "blocked", 0.0, start, trace)

        safe_input = guard.sanitized_input or req.user_input
        intent = self._intent.recognize(safe_input)
        trace.span("intent").finish(intents=intent.intents, confidence=intent.confidence, slots=intent.slots)

        route = self._router.route(intent)
        trace.span("route").finish(action=route.action, primary_intent=route.primary_intent)
        if route.action != "normal":
            return self._response(req, route.message, route.primary_intent, intent.confidence, start, trace)

        session = self._memory.get(req.session_id)
        session.update_from_slots(intent.slots, route.primary_intent)
        tool_result = execute_business_tool(route.primary_intent, intent.slots, safe_input)
        trace.span("tool").finish(tool_result=tool_result[:120])

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", route.system_prompt),
                MessagesPlaceholder("history"),
                (
                    "human",
                    "用户输入：{input}\n识别意图：{intent}\n槽位：{slots}\n业务工具结果：{tool_result}",
                ),
            ]
        )
        answer = (prompt | self._chat_llm).invoke(
            {
                "input": safe_input,
                "intent": intent.intents,
                "slots": intent.slots,
                "tool_result": tool_result,
                "history": session.to_messages(),
            }
        ).content
        trace.span("llm").finish(answer_len=len(answer))

        audit = self._output_auditor.audit(answer)
        trace.span("output_audit").finish(is_safe=audit.is_safe, risk=audit.risk_level)
        if not audit.is_safe:
            answer = "系统生成的回复未通过安全检查，请联系人工客服。"

        session.add_user(req.user_input)
        session.add_ai(answer)
        trace.span("memory_store").finish(stored=True)

        return self._response(req, answer, route.primary_intent, intent.confidence, start, trace)

    def handle_stream(self, req: ChatRequest) -> Generator[str, None, ChatResponse]:
        start = time.time()
        trace = TraceContext(req.trace_id, req.session_id)
        trace.span("receive").finish(user_input=req.user_input[:100], mode="stream")

        guard = self._input_guard.check(req.user_input)
        if not guard.is_safe:
            msg = "输入包含高风险指令，已拒绝处理。"
            yield msg
            return self._response(req, msg, "blocked", 0.0, start, trace)

        safe_input = guard.sanitized_input or req.user_input
        intent = self._intent.recognize(safe_input)
        route = self._router.route(intent)
        if route.action != "normal":
            yield route.message
            return self._response(req, route.message, route.primary_intent, intent.confidence, start, trace)

        session = self._memory.get(req.session_id)
        session.update_from_slots(intent.slots, route.primary_intent)
        tool_result = execute_business_tool(route.primary_intent, intent.slots, safe_input)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", route.system_prompt),
                MessagesPlaceholder("history"),
                (
                    "human",
                    "用户输入：{input}\n识别意图：{intent}\n槽位：{slots}\n业务工具结果：{tool_result}",
                ),
            ]
        )

        full_text = ""
        chain = prompt | self._chat_llm
        for chunk in chain.stream(
            {
                "input": safe_input,
                "intent": intent.intents,
                "slots": intent.slots,
                "tool_result": tool_result,
                "history": session.to_messages(),
            }
        ):
            if chunk.content:
                full_text += chunk.content
                yield chunk.content

        session.add_user(req.user_input)
        session.add_ai(full_text)
        trace.span("stream_done").finish(answer_len=len(full_text), intent=route.primary_intent)
        return self._response(req, full_text, route.primary_intent, intent.confidence, start, trace)

    @staticmethod
    def _response(
        req: ChatRequest,
        answer: str,
        intent: str,
        confidence: float,
        start: float,
        trace: TraceContext,
    ) -> ChatResponse:
        trace.emit()
        return ChatResponse(
            answer=answer,
            intent=intent,
            confidence=confidence,
            session_id=req.session_id,
            trace_id=req.trace_id,
            latency_ms=int((time.time() - start) * 1000),
            prompt_version=PROMPT_VERSION,
        )

