from chat_service import ChatService
from core.protocol import ChatRequest


def run_sync_demo() -> None:
    service = ChatService()
    session_id = "demo-ecommerce"
    questions = [
        "快递到哪了？",
        "订单 123，另外我想改地址。",
        "我的订单号是多少？",
        "那我要退货怎么走？",
        "我很生气，你们客服一直不处理，我要投诉。",
    ]
    for question in questions:
        print(f"\n用户：{question}")
        response = service.handle(ChatRequest(user_input=question, session_id=session_id))
        print(f"助手：{response.answer}")
        print(f"[intent={response.intent}, confidence={response.confidence:.2f}, trace={response.trace_id}]")


def run_stream_demo() -> None:
    service = ChatService()
    req = ChatRequest(user_input="订单 888 的物流到哪了？", session_id="demo-stream")
    print("\n用户：订单 888 的物流到哪了？")
    print("助手：", end="", flush=True)
    stream = service.handle_stream(req)
    try:
        while True:
            print(next(stream), end="", flush=True)
    except StopIteration as done:
        response = done.value
        print()
        if response:
            print(f"[intent={response.intent}, trace={response.trace_id}]")


if __name__ == "__main__":
    run_sync_demo()
    run_stream_demo()

