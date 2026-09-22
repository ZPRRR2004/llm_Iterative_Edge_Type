# Terminal-Bench 2.0 轨迹预处理

从 agentCM 的 trajectory-graph 中分离，只支持 ATIF-v1.7、agent.name=terminus-2。
Python 3.10+，仅依赖标准库。源仓库代码保持不变。

## 运行

在本仓库根目录使用 PowerShell：

```powershell
$env:DEEPSEEK_API_KEY = "你的 API Key"
python -m src.preprocess --input ./trajectory/example.json --output ./runs/preprocess/example
```

可选 `--model`、`--base-url`、`--resume`。模型与服务地址也可通过
`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL` 设置。本入口不自动加载 `.env`。
根 query 提取会调用模型；只有需要拆分未标识聚合 observation 时才额外调用拆分模型。

## Python 接口

```python
from src.preprocess import Client, load, normalize, save

trace, source = load("trajectory/example.json")
result = normalize(trace, source, Client("runs/preprocess/example"))
save("runs/preprocess/example/normalized_trace.json", result)
```

`load` 读取并校验输入；`prepare` 只执行本地字段规范化和输出清理；
`normalize` 提取根 query、执行 prepare、对齐 observation，返回完整规范化字典。
`prepare` 本身不会完成聚合输出拆分，通常下游应使用 `normalize`。

## 保留的行为

- 保留 source、step_id，将 message 保存为 thought；为无效或重复调用 ID 生成替代 ID。
- 复制工具参数，删除 bash_command 的 duration；清除 observation 开头的固定 parser warning。
- source_call_id 本地匹配；单调用直接对齐；多调用无标识输出由模型返回锚点，程序切分原文并验证完整覆盖。
- 拆分使用 thinking=False、temperature=0，校验最多三次尝试；不改变原始轨迹文件。
- 模型请求使用原客户端的敏感值替换、校验、重试和已验证缓存机制。

输出含 source、query、events、review_flags；工具输出位于
`events[*].tool_calls[*].observation.raw`。输出目录还包含
`preprocess_calls.jsonl`、`checkpoint.json` 和 `cache/`。
`--resume` 复用已验证响应缓存，不是从 checkpoint 跳过前面的事件。

## 文件布局

`normalize.py` 是处理主逻辑，`profile.py` 是输入版本约束，`validate.py` 只保留预处理校验，
`deepseek_client.py` 负责模型请求。六个提示词位于模块内的 `src/preprocess/prompts/`，按文件位置加载，
不依赖调用时的工作目录。没有迁入标注、任务归并、依赖建图或可视化模块。
