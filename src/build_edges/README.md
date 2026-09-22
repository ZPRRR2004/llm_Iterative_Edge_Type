# Build Edges

`build_edges` 从 `split` 阶段生成的 Context Window 中，迭代发现可复用的语义 Edge Type，维护一个按发现顺序增长的全局 Registry。

这个模块当前只负责发现、审核和注册 **Edge Type 定义**。它不会在具体事件之间生成 Edge 实例，也不会修改输入 Window。

每个 Window 固定执行三次串行 LLM 调用：

1. **Blind Discovery**：只根据当前 Context Window 独立提出候选类型。
2. **Type Comparison**：把候选类型与进入当前 Window 时的 Registry 快照比较。
3. **Type Review**：结合 Window、候选、比较结果和 Registry 快照，决定最终接受哪些新类型。

只有 Review 接受且通过本地严格校验的类型才会追加到 Registry。一个 Window 的三个阶段始终使用同一个 Prompt 版本和同一份 Registry 快照。

## 模块结构

```text
src/build_edges/
├── __init__.py
├── __main__.py
├── main.py                 # CLI、src/.env 和 config 加载
├── window_loader.py        # Window 校验、排序、序列化和 manifest
├── discovery.py            # Step 1
├── comparison.py           # Step 2
├── review.py               # Step 3
├── llm_client.py           # DeepSeek 请求、retry 和调用记录
├── validator.py            # Window 之外的严格响应/Registry 校验
├── registry.py             # Registry 追加操作
├── prompt_loader.py        # Prompt 校验、渲染和版本管理
├── execution_manager.py    # 阶段编排、批次、人工检查和恢复
├── storage.py              # 原子写入、审计记录和 Registry 重建
├── config.yaml
└── prompts/
    ├── common/granularity_examples.txt
    ├── discovery/system.txt
    ├── discovery/user.txt
    ├── comparison/system.txt
    ├── comparison/user.txt
    ├── review/system.txt
    └── review/user.txt
```

## 环境变量

入口自动读取仓库中的 `src/.env`。至少需要：

```dotenv
DEEPSEEK_API_KEY=your_key
```

可选配置：

```dotenv
DEEPSEEK_MODEL=deepseek-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

加载规则：

- 支持普通的 `KEY=value` 和 `export KEY=value`。
- 支持单引号或双引号包裹的值。
- 支持空行、整行注释和未加引号值末尾的 ` # comment`。
- 如果同名环境变量已经存在，`src/.env` 不会覆盖它。
- `DEEPSEEK_API_KEY` 缺失或为空时，程序在发送请求前终止。
- `DEEPSEEK_MODEL` 未设置时使用 `deepseek-flash`。
- `DEEPSEEK_BASE_URL` 未设置时使用 `https://api.deepseek.com`。

实际请求地址由共享客户端拼为：

```text
{DEEPSEEK_BASE_URL}/chat/completions
```

## 配置文件

默认读取 `src/build_edges/config.yaml`：

```yaml
# 每处理多少个 Window 进行一次人工 Prompt 修改
human_feedback_interval: 10

# 首次调用失败后允许的额外重试次数
max_llm_retries: 3
```

约束：

- 配置文件只能包含这两个整数项。
- 两项都必须存在，不能重复。
- `human_feedback_interval` 必须大于 0。
- `max_llm_retries` 必须大于或等于 0。
- 恢复运行时，配置必须与首次运行保存到 `execution_state.json` 的配置完全相同。

可以通过 `--config` 指定其他配置文件：

```powershell
python -m src.build_edges `
  --input-dir ./runs/09-22_2/split_windows `
  --output-dir ./runs/09-22_2/build_edges `
  --config ./path/to/build_edges.yaml
```

## 输入目录和 Window 契约

`--input-dir` 应指向 `split` 阶段生成的目录。程序只读取该目录第一层的 `*.json`，不会递归读取子目录。

每个文件至少需要满足下面的结构：

```json
{
  "trajectory_id": "trajectory1",
  "window_id": "window_0001",
  "user_query": {
    "title": "任务标题",
    "text": "完整用户请求"
  },
  "previous_summary": "当前窗口之前的轨迹摘要，可以为空字符串",
  "overlap": {
    "event_ids": ["event-0001"],
    "events": [
      {
        "event_id": "event-0001",
        "thought": "..."
      }
    ]
  },
  "core": {
    "event_ids": ["event-0002"],
    "events": [
      {
        "event_id": "event-0002",
        "thought": "..."
      }
    ]
  },
  "future_summary": "当前窗口之后的轨迹摘要，可以为空字符串",
  "metadata": {
    "source_file": "trajectory1.json",
    "window_index": 1
  }
}
```

本地加载器会在任何 LLM 调用之前检查：

- 顶层必须是 JSON Object。
- `trajectory_id` 和 `window_id` 必须是非空字符串。
- `user_query` 必须是 Object，其中 `title` 和 `text` 必须是字符串。
- `previous_summary` 和 `future_summary` 必须是字符串，允许为空。
- `overlap.event_ids` 和 `core.event_ids` 必须是字符串数组。
- `overlap.events` 和 `core.events` 必须是 Object 数组。
- 两个区段中，从 `events` 按顺序取得的 `event_id` 必须与同区段的 `event_ids` 完全一致。
- `core.events` 不能为空；`overlap.events` 可以为空。
- `metadata.window_index` 必须是大于 0 的整数，布尔值不算整数。
- 输入目录必须至少包含一个合法 Window JSON。

`metadata.source_file` 等其他字段可以保留，但当前模块只依赖 `metadata.window_index`。

### 排序、去重和运行目录名

所有 Window 先加载和校验，再按照以下键升序排序：

```text
trajectory_id
metadata.window_index
window_id
filename
```

其中 `trajectory_id`、`window_id` 和文件名按字符串排序，`window_index` 按整数排序。

以下情况会在请求模型前直接报错：

- 两个文件具有相同的 `(trajectory_id, metadata.window_index)`。
- 两个 Window 经过目录名清洗后得到相同的运行目录名。

每个 Window 的输出目录名原始形式为：

```text
{trajectory_id}__{window_id}
```

其中不属于 `A-Z`、`a-z`、`0-9`、`.`、`_`、`-` 的连续字符会替换为 `_`，首尾的 `.` 和 `_` 会被去掉。

### 发送给 LLM 的 Context Window 文本

Window 不会整份原样塞进 Prompt，而是序列化为固定的五段文本：

```text
[USER QUERY]

<user_query 的紧凑 JSON>


[PREVIOUS SUMMARY]

<previous_summary 原文>


[OVERLAP EVENTS]

<overlap.events 的紧凑 JSON>


[CORE EVENTS]

<core.events 的紧凑 JSON>


[FUTURE SUMMARY]

<future_summary 原文>
```

`overlap.event_ids`、`core.event_ids` 和 `metadata` 用于输入校验、排序和追踪，不重复出现在这段 LLM 输入文本里。

## Edge Type 严格结构

Registry、Discovery 的候选、Comparison 的 `new`/`uncertain` 和 Review 的接受结果都使用同一个 Edge Type 结构：

```json
{
  "name": "ATTEMPTS_TO_REPAIR",
  "definition": "A later action attempts to repair an earlier failure.",
  "source_description": "An earlier observed failure.",
  "target_description": "A later action intended to repair that failure."
}
```

校验规则：

- Object 必须且只能包含 `name`、`definition`、`source_description`、`target_description` 四个字段。
- 四个字段都必须是非空字符串。
- `name` 必须匹配 `^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$`。
- 合法名称示例：`ATTEMPTS_TO_REPAIR`、`VERIFY_2_RESULTS`。
- 非法名称示例：`attempts_to_repair`、`ATTEMPTS-TO-REPAIR`、`_VERIFY`。
- 同一个 Edge Type 数组中不能出现重复名称。
- 新接受类型的名称不能与当前 Registry 中已有名称冲突。
- 响应 Object 不允许多余字段。

## 三阶段执行细节

开始一个 Window 时，程序会复制当前 Registry，得到 `registry_snapshot`。下面三个阶段都读取这份快照；即使 Review 最终接受新类型，该新类型也只在三个阶段全部完成后提交。

### Step 1：Blind Discovery

输入：

- 固定格式的完整 Context Window 文本。
- Discovery System Prompt。
- 公共粒度规则和示例。

Discovery 不接收当前 Registry，目的是避免现有类型限制独立发现。

输出必须严格为：

```json
{
  "candidate_edge_types": [
    {
      "name": "ATTEMPTS_TO_REPAIR",
      "definition": "...",
      "source_description": "...",
      "target_description": "..."
    }
  ]
}
```

`candidate_edge_types` 可以为空数组。顶层不能包含解释、统计或其他字段。

### Step 2：Type Comparison

输入：

- Discovery 产生的完整候选数组。
- 当前 Window 开始时的完整 Registry 快照。
- Comparison System Prompt。
- 公共粒度规则和示例。

输出必须严格为：

```json
{
  "existing": [
    {
      "candidate_name": "ATTEMPTS_TO_REPAIR",
      "matched_existing_name": "REPAIRS_FAILURE"
    }
  ],
  "new": [
    {
      "name": "VERIFIES_REPAIR",
      "definition": "...",
      "source_description": "...",
      "target_description": "..."
    }
  ],
  "uncertain": []
}
```

本地校验保证：

- 顶层必须且只能包含 `existing`、`new`、`uncertain`。
- 三个字段都必须是数组。
- `existing` 中每项必须且只能包含 `candidate_name` 和 `matched_existing_name`。
- `candidate_name` 必须来自本次 Discovery 候选名称。
- `matched_existing_name` 必须真实存在于 Registry 快照。
- `new` 和 `uncertain` 中每项必须满足完整 Edge Type 结构，名称必须来自候选名称。
- 每一个候选名称必须在三个分类中出现且只出现一次，不能遗漏、额外添加或重复分类。
- Registry 为空时，`existing` 和 `uncertain` 必须为空，全部候选必须进入 `new`。

### Step 3：Type Review

输入：

- 完整 Context Window 文本。
- Discovery 候选数组。
- Comparison 的完整结果。
- 当前 Window 开始时的 Registry 快照。
- Review System Prompt。
- 公共粒度规则和示例。

输出必须严格为：

```json
{
  "accepted_edge_types": [
    {
      "name": "VERIFIES_REPAIR",
      "definition": "...",
      "source_description": "...",
      "target_description": "..."
    }
  ]
}
```

本地校验保证：

- 顶层必须且只能包含 `accepted_edge_types`。
- 接受列表中的每项必须满足完整 Edge Type 结构。
- 接受列表内部不能有重复名称。
- 接受类型名称不能已存在于 Registry 快照。
- Discovery 候选为空时，Review 不能接受任何新类型。

Review 可以拒绝全部候选，此时返回空数组。

### Commit

Review 通过后，程序执行本地 Commit：

1. 再次校验 Registry 快照和 `accepted_edge_types`。
2. 按 Review 返回顺序把接受类型追加到 Registry 末尾。
3. 把 Window `metadata.json` 标记为 `completed`。
4. 原子保存新的 `edge_type_registry.json`。
5. 增加 `completed_windows` 和 `next_window_index`。

Registry 不会按名称重新排序，顺序就是类型被接受和提交的顺序。

## Prompt 组成、变量和版本

模块包含七个可编辑 Prompt 文件：

| 文件 | 用途 | 允许且必须存在的模板变量 |
| --- | --- | --- |
| `common/granularity_examples.txt` | 三阶段共享的粒度规则与示例 | 无 |
| `discovery/system.txt` | Discovery System Prompt | 无 |
| `discovery/user.txt` | Discovery User Prompt | `{{context_window}}` |
| `comparison/system.txt` | Comparison System Prompt | 无 |
| `comparison/user.txt` | Comparison User Prompt | `{{candidate_edge_types}}`、`{{existing_registry}}` |
| `review/system.txt` | Review System Prompt | 无 |
| `review/user.txt` | Review User Prompt | `{{context_window}}`、`{{candidate_edge_types}}`、`{{comparison_results}}`、`{{existing_registry}}` |

每次调用的 System Message 按下面方式拼接：

```text
<当前阶段 system.txt>

<common/granularity_examples.txt>
```

User Message 只替换上表列出的双花括号变量。缺少变量、出现未知变量、文件缺失或内容为空都会拒绝运行。

首次运行时：

1. 读取并校验 `src/build_edges/prompts/` 下的七个文件。
2. 把完整快照保存为输出目录中的 `prompt_versions/v0001/`。
3. 第一批全部使用 `v0001`。

每次人工批次检查按 Enter 后：

1. 重新读取源码目录中的七个 Prompt。
2. 重新执行完整文件和模板变量校验。
3. 校验失败时停留在当前检查点，提示修正后再次按 Enter。
4. 校验通过后保存下一个版本，如 `v0002`。
5. 即使文件内容没有变化，也保存新的版本快照，以记录下一批实际使用的 Prompt。

恢复运行时，程序先从输出目录的 `prompt_versions/{state.prompt_version}/` 加载历史版本，避免源码 Prompt 后续修改导致同一批次前后不一致。只有跨过人工检查点后，才读取当前源码 Prompt 并生成下一版本。

## DeepSeek 请求参数和上下文保护

每个阶段发送非流式 Chat Completions 请求，核心参数为：

```json
{
  "response_format": {"type": "json_object"},
  "max_tokens": 32768,
  "thinking": {"type": "enabled"},
  "reasoning_effort": "high",
  "stream": false
}
```

其他运行参数：

- 单次 HTTP 超时：600 秒。
- 上下文容量上限：1048576。
- 发送前的保守容量估计：`UTF-8(messages JSON) 字节数 + 1024 + max_tokens`。
- 如果估计值超过容量上限，立即失败并保存容量错误，不裁剪 Window、Registry 或 Prompt。
- 只有 `finish_reason == "stop"` 的响应才视为完整响应。
- 响应使用严格 JSON 解析；重复 JSON Key、`NaN`、`Infinity` 等非有限常量都会被拒绝。

共享 `src/deepseek_client.py` 的内部 HTTP retry 在本模块中被设置为 0，由 `build_edges` 的阶段级 retry 统一控制，避免两层重试相乘。

请求和记录写盘前会使用共享 Redactor 隐藏已配置 API Key 及若干常见凭证格式。模型响应解析完成后会恢复本次输入中由 Redactor 替换的占位符，再进入结构校验。

## Retry 的精确行为

`max_llm_retries` 表示首次请求失败后的额外尝试次数：

| 配置值 | 同一阶段最多请求次数 |
| ---: | ---: |
| 0 | 1 |
| 1 | 2 |
| 3 | 4 |

以下情况都会使当前 attempt 失败并进入下一次阶段级 retry：

- 网络请求错误或超时。
- HTTP 错误。
- Provider 响应结构缺少 `choices[0]` 或 `message.content`。
- `finish_reason` 不是 `stop`。
- Content 不是严格合法 JSON。
- JSON 不满足当前阶段的本地结构或一致性校验。

重试使用相同的 System/User Message 和请求参数，当前实现不修改 Prompt，也不对阶段级 retry 增加等待退避。

每次失败会在终端打印：

- 当前 Window。
- 当前阶段。
- 失败原因。
- 还会执行第几次 retry。

全部尝试失败后：

1. 保存该阶段的失败调用记录。
2. 把当前 Window `metadata.json` 标记为 `failed`，记录 `failed_stage` 和错误。
3. 把全局 `execution_state.json` 标记为 `failed`。
4. 终止整个运行，不继续后面的 Window。

修复网络、配置或 Prompt 问题后，可以用 `--resume` 从失败阶段继续。已经成功的前置阶段不会重新请求。

如果一个阶段在恢复时再次写入同名 request/response 文件，旧记录会移入新 response 文件的 `previous_calls` 数组，不会静默丢失先前失败记录。

## 运行命令

### 首次运行

输入、输出目录必须位于 `src/build_edges` 之外。输出目录可以不存在；如果已经存在，则必须为空。

```powershell
python -m src.build_edges `
  --input-dir ./runs/09-22_2/split_windows `
  --output-dir ./runs/09-22_2/build_edges
```

也可以直接运行：

```powershell
python ./src/build_edges/main.py `
  --input-dir ./runs/09-22_2/split_windows `
  --output-dir ./runs/09-22_2/build_edges
```

如果已经把 `src` 加入 `PYTHONPATH`，也可以使用：

```powershell
python -m build_edges.main `
  --input-dir ./runs/09-22_2/split_windows `
  --output-dir ./runs/09-22_2/build_edges
```

### 中断或失败后恢复

```powershell
python -m src.build_edges `
  --input-dir ./runs/09-22_2/split_windows `
  --output-dir ./runs/09-22_2/build_edges `
  --resume
```

恢复时必须继续使用原来的输入目录、输出目录和配置。不要为 `--resume` 新建空输出目录。

## 运行期间为什么可能长时间没有终端输出

当前实现不使用流式响应，也不打印每个成功阶段的“开始/完成”日志。成功请求进行期间，终端可以长时间没有任何新内容。

例如，20 个 Window 会串行执行 60 个 DeepSeek 阶段请求：

```text
20 Window × 3 stages = 60 requests
```

单次请求最多等待 600 秒；如果失败，默认最多额外 retry 3 次。因此终端静默通常表示正在等待 DeepSeek，并不等于 Python 本地死循环。

阶段的 `*_request.json` 和 `*_response.json` 是在该阶段返回或最终失败后一起保存的。正在飞行中的请求不会提前产生 request 文件，也不会逐 attempt 实时更新 response 文件。

### 查看全局状态

在另一个 PowerShell 中执行：

```powershell
Get-Content -Raw -Encoding utf8 ./runs/09-22_2/build_edges/execution_state.json
```

示例：

```json
{
  "next_window_index": 3,
  "completed_windows": 3,
  "current_batch_index": 1,
  "completed_windows_in_batch": 3,
  "prompt_version": "v0001",
  "next_stage": "comparison",
  "status": "running",
  "config": {
    "human_feedback_interval": 10,
    "max_llm_retries": 3
  }
}
```

字段含义：

| 字段 | 含义 |
| --- | --- |
| `next_window_index` | 当前要处理或恢复的 Window 在排序后列表中的零基索引 |
| `completed_windows` | 已完成三个阶段并提交 Registry 的 Window 数量 |
| `current_batch_index` | 当前批次编号，从 1 开始 |
| `completed_windows_in_batch` | 当前批次已经提交的 Window 数量 |
| `prompt_version` | 当前批次使用的 Prompt 快照版本 |
| `next_stage` | 当前 Window 下一步要执行或恢复的阶段 |
| `status` | 全局执行状态 |
| `config` | 首次运行使用的配置副本 |

`next_stage` 的值：

| 值 | 含义 |
| --- | --- |
| `discovery` | 当前 Window 尚未成功完成 Discovery |
| `comparison` | Discovery 已保存，下一步是 Comparison |
| `review` | Discovery 和 Comparison 已保存，下一步是 Review |
| `commit` | 三次模型调用均已保存，下一步只需本地提交 Registry |

全局 `status` 的值：

| 值 | 含义 |
| --- | --- |
| `running` | 正在本地处理、等待 DeepSeek，或上次被 Ctrl+C 中断时停留在运行态 |
| `waiting_for_enter` | 一批完成，原终端正等待人工查看和按 Enter |
| `failed` | 某阶段全部尝试失败或发生其他异常，可以排查后恢复 |
| `completed` | 所有 Window 和最后批次均已保存 |

### 查看最近落盘文件

```powershell
Get-ChildItem ./runs/09-22_2/build_edges/runs -Recurse -File |
  Sort-Object LastWriteTime |
  Select-Object -Last 15 FullName, Length, LastWriteTime
```

如果同一 Window 已有 Discovery 文件和 Comparison 文件，但没有 Review 文件，通常表示正在等待 Review 返回。应同时结合 `execution_state.json` 和 Python 进程是否存在判断。

### 查看 Python 进程

```powershell
Get-Process python -ErrorAction SilentlyContinue |
  Select-Object Id, CPU, StartTime, Responding, Path
```

网络等待期间 CPU 很低是正常现象。

## 每批人工检查和 Prompt 修改

达到 `human_feedback_interval` 后，程序先把当前 Registry 和本批结果完整写盘，再把状态设置为 `waiting_for_enter`。终端会显示：

- 已处理 Window 数。
- 本批新增 Edge Type 数。
- 当前 Registry 总数。
- 当前 Prompt 版本。
- `edge_type_registry.json` 路径。
- 本批 `review_packet.md` 路径。
- 七个可修改 Prompt 文件的路径。

此时可以：

1. 打开 `batches/batch_NNNN/review_packet.md` 检查本批新类型和完整 Registry。
2. 按需修改 `src/build_edges/prompts/` 下的 Prompt。
3. 回到原运行终端按 Enter。

按 Enter 后才会重新加载和校验 Prompt。校验失败时不会丢失 Registry，也不会进入下一批；程序会提示错误并继续等待修改和下一次 Enter。

每个完整批次都会暂停。最后不足一个批次的剩余 Window 仍会保存 batch 目录，但全部输入完成后直接退出，不再等待 Enter。

如果程序恰好在 `waiting_for_enter` 时被关闭，使用 `--resume` 后会重新显示人工检查流程，然后再进入下一批。

## 输出目录完整结构

```text
build_edges/
├── edge_type_registry.json
├── execution_state.json
├── window_manifest.json
├── prompt_versions/
│   ├── v0001/
│   │   ├── common/granularity_examples.txt
│   │   ├── discovery/system.txt
│   │   ├── discovery/user.txt
│   │   ├── comparison/system.txt
│   │   ├── comparison/user.txt
│   │   ├── review/system.txt
│   │   └── review/user.txt
│   └── v0002/
│       └── ...
├── runs/
│   ├── trajectory1__window_0001/
│   │   ├── metadata.json
│   │   ├── discovery_request.json
│   │   ├── discovery_response.json
│   │   ├── comparison_request.json
│   │   ├── comparison_response.json
│   │   ├── review_request.json
│   │   └── review_response.json
│   └── trajectory1__window_0002/
│       └── ...
└── batches/
    ├── batch_0001/
    │   ├── registry_before.json
    │   ├── registry_after.json
    │   ├── newly_accepted_edge_types.json
    │   ├── batch_metadata.json
    │   └── review_packet.md
    └── batch_0002/
        └── ...
```

### `edge_type_registry.json`

当前完整 Registry，是 Edge Type Object 数组。首次运行从空数组开始。每个 Window Commit 后更新一次。

```json
[
  {
    "name": "ATTEMPTS_TO_REPAIR",
    "definition": "...",
    "source_description": "...",
    "target_description": "..."
  }
]
```

### `window_manifest.json`

首次运行保存输入身份和顺序：

```json
{
  "input_directory": "输入目录的绝对路径",
  "windows": [
    {
      "global_index": 0,
      "filename": "trajectory1__window_0001.json",
      "trajectory_id": "trajectory1",
      "window_id": "window_0001",
      "window_index": 1,
      "run_name": "trajectory1__window_0001",
      "sha256": "原始输入文件字节的 SHA-256"
    }
  ]
}
```

恢复时会重新生成 manifest 并要求与保存版本完全一致。因此下列变化都会拒绝恢复：

- 增加、删除或重命名 Window 文件。
- 修改任一输入文件的字节内容。
- 改变 `trajectory_id`、`window_id` 或 `window_index` 导致顺序变化。
- 把相同输入文件移动到另一个输入目录，因为 `input_directory` 绝对路径也参与比较。

### `execution_state.json`

记录全局进度、批次、Prompt 版本、下一阶段、状态和配置。每个成功阶段、每个 Window Commit、进入或离开人工检查点时都会原子更新。

### `runs/<run_name>/metadata.json`

记录单个 Window 的事务状态，主要字段包括：

- 输入文件名、`trajectory_id`、`window_id` 和 `global_index`。
- 当前 Window 固定使用的 `prompt_version`。
- Window 开始时复制的完整 `registry_snapshot`。
- `completed_stages`。
- 最终 `accepted_edge_types`。
- `registry_size_after`。
- `status`、`failed_stage` 和 `error`。
- 创建、更新和完成时间。

恢复时会校验其中的 Prompt 版本和 Registry 快照是否与全局状态推导结果一致。

### `*_request.json`

每个阶段一份，记录：

- `stage`。
- `window_file`。
- `prompt_version`。
- `model`。
- `started_at`。
- 实际发送的 `system_message` 和 `user_message`。
- `max_tokens`、thinking、reasoning effort 和 response format。

### `*_response.json`

每个阶段一份，记录：

- 是否成功和完成时间。
- 阶段总耗时。
- `attempt_count`。
- 每次 attempt 的开始时间、耗时、Provider 原始响应、Content 和错误。
- 通过校验后的 `parsed_response`。
- 恢复或重跑同阶段时保存的 `previous_calls`。

这些文件用于审计实际 Prompt、模型原始返回和本地校验结果。文件可能较大，因为 `raw_response` 和实际消息会完整保留；已识别的凭证会被 Redactor 替换。

### `batches/batch_NNNN/`

- `registry_before.json`：本批开始前的 Registry。
- `registry_after.json`：本批全部 Window 提交后的 Registry。
- `newly_accepted_edge_types.json`：按名称比较前后 Registry 得到的本批新增类型。
- `batch_metadata.json`：批次编号、处理 Window 范围、Prompt 版本、新增数量、Registry 大小和保存时间。
- `review_packet.md`：便于人工阅读的批次信息、新增类型和当前完整 Registry。

## 断点恢复保证

恢复命令不会简单地从头重跑，而是按已经落盘的事务状态继续：

1. 校验当前输入 manifest 与首次运行完全一致。
2. 校验当前 config 与首次运行完全一致。
3. 从前 `completed_windows` 个 Window 的 `metadata.json` 重新构建 Registry。
4. 重建结果会覆盖 `edge_type_registry.json`，修正 Registry 已写但全局状态尚未推进等中断情况。
5. 从 `prompt_versions/{prompt_version}` 加载历史 Prompt。
6. 根据 `next_window_index` 定位 Window。
7. 根据 `next_stage` 跳过已经成功并保存的阶段。
8. 从对应 `*_response.json` 读取并重新校验已完成阶段的 `parsed_response`。
9. 从 Discovery、Comparison、Review 或本地 Commit 继续。

如果状态是：

- `failed`：先改回运行态，再从保存的失败阶段重试。
- `waiting_for_enter`：先恢复人工 Prompt 检查流程。
- `completed`：打印已经完成并直接返回，不重复请求。
- `running`：按最后保存的 Window 和阶段继续，适用于 Ctrl+C 或进程异常退出。

Registry 以每个已提交 Window 的 `accepted_edge_types` 为恢复事实来源。重建时若发现 Window 未完整提交、接受列表结构错误或跨 Window 出现重复名称，会拒绝继续。

## 原子写入

JSON、状态、Registry、调用记录和 Review Packet 都采用以下流程：

1. 先写同目录的 `.tmp` 文件。
2. 再使用 `os.replace` 原子替换目标文件。
3. Windows 上如果替换暂时得到 `PermissionError`，最多短暂重试 5 次。

Prompt 版本先写入 `vNNNN.tmp/` staging 目录，全部文件成功后再整体改名为正式版本目录。已有 Prompt 版本不会覆盖。

原子写入可以避免普通中断留下半个 JSON，但不会支持两个进程同时写同一个输出目录。

## 并发限制

模块是单进程、单 Window、单阶段串行执行。不要在原进程仍运行时，对同一个 `--output-dir` 再启动普通运行或 `--resume`。两个进程可能同时写入：

- `execution_state.json`
- `edge_type_registry.json`
- 同一个 Window 的 request/response
- 同一个 Prompt 版本目录

需要中断时，在原终端按 Ctrl+C。确认原 Python 进程已经退出后，再对原输出目录执行 `--resume`。

## 常见错误

### 输出目录非空

首次运行要求输出目录为空。如果目录中已有执行记录，应使用 `--resume`；如果是另一轮任务，应换一个新的输出目录。

### `src/.env` 已配置但仍提示缺少 Key

检查变量名必须是 `DEEPSEEK_API_KEY`，并确认值不是空字符串。系统中已存在的同名环境变量优先于 `src/.env`。

### Prompt 校验失败

检查七个文件是否都存在且非空，并确保 User Prompt 精确保留各自要求的 `{{...}}` 变量。System Prompt 和公共 Prompt 不能增加模板变量。

### Comparison 一直重试

查看 `comparison_response.json` 中每个 attempt 的 `error`。常见原因是候选没有全部分类、同一候选出现在多个分类、匹配了不存在的 Registry 名称，或者 Registry 为空时没有把全部候选放进 `new`。

### Review 一直重试

查看 Review attempt 的本地校验错误。常见原因是输出包含多余字段、Edge Type 名称格式错误、接受列表内部重名，或者接受了 Registry 中已有名称。

### `--resume` 提示输入发生变化

恢复要求输入目录绝对路径、文件集合、顺序和每个文件的 SHA-256 全部一致。恢复期间不要重新执行会覆盖 `split_windows` 的上游步骤。

### `--resume` 提示 Config 不一致

使用首次运行时相同的 `human_feedback_interval` 和 `max_llm_retries`。如果需要改变配置，应新建输出目录重新开始一轮。

### 终端停在第 10、20、30 个 Window

当还有后续 Window 时，这是人工 Prompt 检查点。查看终端给出的 Registry 和 Review Packet，必要时修改 Prompt，然后在原终端按 Enter。

### 终端无输出但进程仍在

先读取 `execution_state.json`，再查看最近阶段文件和 Python 进程。请求阶段最长可以等待 600 秒，且成功请求期间默认不打印进度。

## 临时验证文件

模块的临时验证代码和数据位于仓库 `temp/build_edges_tests/`，由 `.gitignore` 排除，不属于正式模块源码。
