"""
灵语 - 第2步：完整对话链路
架构：意图识别 → 路由分发 → 记忆管理 → 模型执行
"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

load_dotenv()

# ============================================================
# 第一层：LLM（大脑）
# ============================================================
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.3,  # 客服场景用低温度，回答更稳定
)


# ============================================================
# 第二层：记忆管理（病历本）
# 每次 LLM 调用都是独立的，它不记得上一句说了什么。
# 记忆层的职责：把历史对话存起来，下次调用时一起发过去。
# ============================================================
@dataclass
class SessionState:
    """会话状态 - 管理多轮对话的历史"""

    session_id: str                    # 区分不同用户的会话
    history: List[BaseMessage] = field(default_factory=list)  # 对话历史

    def add_user(self, text: str):
        """记录用户说了什么"""
        self.history.append(HumanMessage(content=text))

    def add_ai(self, text: str):
        """记录 AI 回复了什么"""
        self.history.append(AIMessage(content=text))

    def get_history(self, window: int = 6) -> List[BaseMessage]:
        """
        返回最近 N 轮对话。
        window=6 意味着只看最近 3 轮问答（一问一答算一轮，占 2 条消息）。
        为什么要裁剪？因为历史越长 Token 消耗越大，还占上下文窗口。
        """
        return self.history[-window * 2:]  # N轮 × 2(一问一答)


# ============================================================
# 第三层：意图识别 + 工具（分诊台 + 业务处理）
# 先用简单的关键词匹配来做意图判断，后续会升级为 LLM 判断
# ============================================================
def route_intent(text: str) -> str:
    """判断用户的意图"""
    if "物流" in text or "快递" in text or "到哪" in text:
        return "track_shipping"
    if "地址" in text or "改地址" in text or "换地址" in text:
        return "change_address"
    if "退货" in text or "退款" in text or "退" in text:
        return "return_policy"
    return "general_qa"  # 默认兜底


def handle_track_shipping(text: str) -> str:
    """物流查询 - 这里模拟返回，实际应该调快递公司 API"""
    return "您的包裹已出库，正在运输中（预计 3 天内送达）。如需更精确的位置，请提供订单号。"


def handle_change_address(text: str) -> str:
    """改地址 - 这里模拟返回"""
    return "已为您记录地址修改申请。请提供新地址和订单号，我将为您更新。"


def handle_return_policy(text: str) -> str:
    """退货政策 - 这里模拟返回"""
    return "根据退货政策：签收后 7 天内可申请无理由退货，商品需保持原样。需要我为您发起退货流程吗？"


def handle_general_qa(text: str) -> str:
    """通用问答 - 没有匹配到业务意图时，让 LLM 自己发挥"""
    return ""  # 返回空字符串，表示不需要工具结果，让 LLM 自由回答


# 意图 → 处理函数的映射表（路由注册表）
HANDLERS = {
    "track_shipping": handle_track_shipping,
    "change_address": handle_change_address,
    "return_policy": handle_return_policy,
    "general_qa": handle_general_qa,
}


# ============================================================
# 第四层：Pipeline（流水线组装）
# 用 LCEL（LangChain Expression Language）把各层串起来
# | 符号是 LangChain 的管道操作符，前一个的输出是后一个的输入
# ============================================================

# Step A：路由步骤 — 判断意图，调用对应的工具函数
def run_tool(inputs: dict) -> dict:
    """根据意图调用对应的工具，把结果加到 inputs 里"""
    intent = inputs["intent"]
    handler = HANDLERS.get(intent, handle_general_qa)
    tool_result = handler(inputs["input"])
    return {**inputs, "tool_result": tool_result}


# Step B：拼 Prompt — 把记忆、工具结果、当前问题组合成发给 LLM 的消息
prompt = ChatPromptTemplate.from_messages([
    # 系统角色：告诉 LLM 它是什么身份、要遵守什么规则
    ("system", "你是「灵语」电商客服助手。"
               "回答要简洁友好。"
               "如果工具结果不为空，优先使用工具结果回答；"
               "如果工具结果为空，用自己的知识回答。"),

    # 历史对话占位符：运行时从这里注入历史消息
    MessagesPlaceholder("history"),

    # 当前用户问题 + 工具结果
    ("human", "用户问题：{input}\n工具查询结果：{tool_result}"),
])


# Step C：完整流水线
# 执行顺序：route_intent → run_tool → prompt → llm
# RunnableLambda 是把普通 Python 函数包装成 LangChain 组件
def build_chain(state: SessionState):
    """构建完整的对话链路"""

    # 第1步：判断意图
    router = RunnableLambda(lambda x: {
        "input": x,
        "intent": route_intent(x),
        "history": state.get_history(),  # 注入历史记忆
        "tool_result": "",               # 占位，下一步填充
    })

    # 用 | 串联：路由 → 工具执行 → 拼Prompt → LLM推理
    chain = router | RunnableLambda(run_tool) | prompt | llm
    return chain


# ============================================================
# 运行
# ============================================================
if __name__ == "__main__":
    # 创建会话
    session = SessionState(session_id="demo")

    # 第 1 轮
    q1 = "快递到哪了？"
    print(f"\n用户：{q1}")

    chain = build_chain(session)
    # 调用链路：q1 → route_intent("track_shipping") → run_tool → prompt → llm
    a1 = chain.invoke(q1)

    # 记住这轮对话
    session.add_user(q1)
    session.add_ai(a1.content)

    print(f"灵语：{a1.content}")
    print(f"[意图：{route_intent(q1)}]")

    # 第 2 轮 — 用户追问，验证记忆是否生效
    q2 = "那我想改地址"
    print(f"\n用户：{q2}")

    # 重新构建链路（此时 session 里已经有了第 1 轮的对话历史）
    chain2 = build_chain(session)
    a2 = chain2.invoke(q2)

    session.add_user(q2)
    session.add_ai(a2.content)

    print(f"灵语：{a2.content}")
    print(f"[意图：{route_intent(q2)}]")

    # 第 3 轮 — 测试通用问答（没有匹配的业务意图）
    q3 = "推荐一款适合编程的笔记本电脑"
    print(f"\n用户：{q3}")

    chain3 = build_chain(session)
    a3 = chain3.invoke(q3)

    session.add_user(q3)
    session.add_ai(a3.content)

    print(f"灵语：{a3.content}")
    print(f"[意图：{route_intent(q3)}]")
