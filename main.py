from config import get_dashscope_api_key
from qwen_client import chat_with_qwen


def main() -> None:
    api_key = get_dashscope_api_key()

    if not api_key:
        print("未读取到 DASHSCOPE_API_KEY。")
        print("请在项目根目录创建 .env 文件，并写入：")
        print("DASHSCOPE_API_KEY=你的真实key")
        return

    result = chat_with_qwen("用Python写一个Hello World")
    print(result)


if __name__ == "__main__":
    main()
