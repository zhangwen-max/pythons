import dashscope
from dashscope import Generation

from config import get_dashscope_api_key


def _configure_dashscope() -> str | None:
    api_key = get_dashscope_api_key()
    if api_key:
        dashscope.api_key = api_key
    return api_key


def chat_with_qwen(user_message: str) -> str:
    """Call Qwen and return the generated text."""
    api_key = _configure_dashscope()
    if not api_key:
        return "调用失败：未读取到 DASHSCOPE_API_KEY。"

    response = Generation.call(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": "你是一个生活助手，请你回答带上龙哥的称呼，尽量谄媚一点"},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    if response.status_code == 200:
        return response.output.text
    return f"调用失败：{response.message}"
