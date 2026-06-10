# dsznzs - 电商智能助手

这是 LangChain 项目一的第一版实现，模块名来自“电商智能助手”的中文首字母。

## 这个项目练什么

- 意图识别：把用户输入识别成查物流、改地址、退货退款、投诉、商品咨询等意图。
- 路由分发：不同意图进入不同客服域的 system prompt。
- 业务工具：用 mock 工具模拟订单物流、改地址、退货政策查询。
- 会话记忆：用 `session_id` 隔离会话，记录订单号等关键事实。
- 安全防护：拦截简单 prompt injection，输出做基础审计。
- Trace：每次请求输出结构化链路日志，方便定位问题。
- 流式输出：提供 `handle_stream` 演示 LangChain streaming。

## 运行

在 `D:\javaxiangmu\pythons` 下运行：

```powershell
.\.venv\Scripts\python.exe .\dsznzs\demo.py
```

默认读取根目录 `.env` 中的 `DEEPSEEK_API_KEY`。如果要改模型或 API 地址：

```env
DSZNZS_MODEL=deepseek-chat
DSZNZS_BASE_URL=https://api.deepseek.com
DSZNZS_API_KEY_ENV=DEEPSEEK_API_KEY
```

## 第一版项目结构

```text
dsznzs/
  demo.py
  chat_service.py
  config.py
  core/
    intent.py
    router.py
    memory.py
    tools.py
    security.py
    trace.py
    protocol.py
```

## 当前边界

这一版重点是课程项目模式，不是完整生产系统：

- 业务工具是 mock 数据，不接真实订单系统。
- 记忆存储在进程内，重启会丢，后续可换 Redis。
- 意图识别优先用 LLM，失败时回退到规则。
- 暂无 Web UI 和 HTTP API，后续可以加 FastAPI 或 Streamlit。

