import os

import dashscope
from dashscope import Generation
from dotenv import load_dotenv


def load_dashscope_api_key() -> str | None:
    """Load the DashScope API key from the local .env file."""
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        dashscope.api_key = api_key
    return api_key


def chat_with_qwen(user_message: str) -> str:
    """Call Qwen and return the generated text."""
    response = Generation.call(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": "你是一个 生活 助手，请你回答带上龙哥的称呼，尽量谄媚一点"},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    if response.status_code == 200:
        return response.output.text
    return f"调用失败：{response.message}"


if __name__ == "__main__":
    api_key = load_dashscope_api_key()

    if not api_key:
        print("未读取到 DASHSCOPE_API_KEY。")
        print("请在项目根目录创建 .env 文件，并写入：")
        print("DASHSCOPE_API_KEY=你的真实key")
    else:
        result = chat_with_qwen("用Python写一个Hello World")
        print(result)
