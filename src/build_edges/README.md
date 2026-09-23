# Build Edges

`build_edges` 从 `split` 阶段生成的 Context Window 中，迭代发现可复用的语义 Edge Type，并通过批次级 Human Feedback 维护一个持续演化的全局 Registry。

这个模块当前只负责发现、审核和注册 **Edge Type 定义**。它不会在具体事件之间生成 Edge 实例，也不会修改输入 Window。

每个 Window 固定执行三次串行 LLM 调用：

1. **Blind Discovery**：只根据当前 Context Window 独立提出候选类型。
2. **Type Comparison**：把候选类型与进入当前 Window 时的 Registry 快照比较。
3. **Type Review**：结合 Window、候选、比较结果和 Registry 快照，决定新增类型，并修订本轮 `existing` 匹配到的已有类型。

Review 的新增和修订通过本地严格校验后，在一次 Registry 更新中生效。一个 Window 的三个阶段始终使用同一个 Prompt 版本和同一份 Registry 快照。

每完成一个非最终的完整批次，程序根据 `feedback_mode` 执行一种人工反馈流程：

- `manual_prompt`：人工修改三阶段 Prompt，Registry 保持不变。
- `registry_feedback`：人工输入自然语言意见，由 Registry Revision LLM 对完整 Registry 执行 `KEEP`、`DELETE`、`REVISE`、`MERGE`，Prompt 版本保持不变。

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
├── registry_revision.py    # Human Feedback 驱动的完整 Registry Revision
├── llm_client.py           # DeepSeek 请求、retry 和调用记录
├── validator.py            # Window 之外的严格响应/Registry 校验
├── registry.py             # Window Review 更新及批次 Revision Plan 应用
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
    ├── review/user.txt
    ├── registry_revision/system.txt
    └── registry_revision/user.txt
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
# 每处理多少个 Window 进行一次 Human Feedback
human_feedback_interval: 10

# manual_prompt 或 registry_feedback
feedback_mode: registry_feedback

# 首次调用失败后允许的额外重试次数
max_llm_retries: 3
```

约束：

- 配置文件必须且只能包含这三个配置项，不能重复。
- `human_feedback_interval` 必须大于 0。
- `feedback_mode` 必须是 `manual_prompt` 或 `registry_feedback`。
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
- 更新后的完整 Registry 不能有重复名称；如果已有类型在本轮修订时改名，新类型可以使用它让出的原名称。
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
  ],
  "revised_existing_edge_types": [
    {
      "original_name": "REPAIRS_FAILURE",
      "revised_edge_type": {
        "name": "ATTEMPTS_TO_REPAIR",
        "definition": "...",
        "source_description": "...",
        "target_description": "..."
      }
    }
  ]
}
```

本地校验保证：

- 顶层必须且只能包含 `accepted_edge_types` 和 `revised_existing_edge_types`，两者都必须是数组。
- 接受列表中的每项必须满足完整 Edge Type 结构。
- 接受列表内部不能有重复名称。
- `revised_existing_edge_types` 中每项必须且只能包含 `original_name` 和完整四字段 `revised_edge_type`。
- `original_name` 必须出现在本轮 Comparison 的 `existing.matched_existing_name` 中，也必须存在于 Window 开始时的 Registry 快照；同一个原类型最多修订一次。
- 对“修订后的全部已有类型 + 新增类型”统一检查名称唯一性。已有类型改名后，原名称可以由另一个新类型使用。
- Discovery 候选为空时，两个输出数组都必须为空。

Review 会重新评估三个 Comparison 分类：先前判为 `existing` 的候选也可能作为真正的新关系被接受；对应的已有类型只有在含义相同但定义需要改进时才修订。Review 可以同时返回新增和修订，也可以让两个数组都为空。候选与已有类型的语义一致性由 Prompt 复核；本地校验只检查可以确定的结构与名称约束。

### Commit

Review 通过后，程序执行本地 Commit：

1. 再次校验完整 Review Result。
2. 按 `original_name` 在快照中原位替换已有类型；其余已有类型原样保留。
3. 按 Review 返回顺序把接受的新类型追加到 Registry 末尾。
4. 校验更新后的完整 Registry，再把 Window `metadata.json` 标记为 `completed`。
5. 原子保存新的 `edge_type_registry.json`，增加 `completed_windows` 和 `next_window_index`。

Registry 不会按名称重新排序。已有类型修订保留原位置，新类型按本轮接受顺序追加。逐 Window 的已有类型修订与批次级 `registry_feedback` 独立，适用于两种反馈模式。

## Registry Feedback 与 Revision Plan

`feedback_mode: registry_feedback` 时，程序在每个非最终的完整批次后读取多行自然语言反馈。用户逐行输入内容，最后单独输入：

```text
END
```

程序把下面四部分组成一次新的非流式 LLM 请求：

```text
System Message
= registry_revision/system.txt
+ common/granularity_examples.txt

User Message
= Human Feedback
+ 当前完整 Edge Type Registry
```

Revision 处理的是批次 Window 全部提交后的**完整 Registry**，并非只处理本批新增类型。

LLM 必须为输入 Registry 中每个类型指定且仅指定一个操作：

| 操作 | 含义 | 额外字段 |
| --- | --- | --- |
| `KEEP` | 原始四字段对象完全不变地保留 | 无 |
| `DELETE` | 删除该独立类型 | 无 |
| `REVISE` | 用一个完整的新四字段类型替换原类型，允许改名 | `revised_edge_type` |
| `MERGE` | 当前类型不再独立存在，其语义归入另一个原始 Registry 类型 | `merge_into` |

输出顶层必须严格为：

```json
{
  "revisions": [
    {
      "original_name": "TYPE_A",
      "operation": "KEEP"
    },
    {
      "original_name": "TYPE_B",
      "operation": "DELETE"
    },
    {
      "original_name": "TYPE_C",
      "operation": "REVISE",
      "revised_edge_type": {
        "name": "TYPE_C_REVISED",
        "definition": "...",
        "source_description": "...",
        "target_description": "..."
      }
    },
    {
      "original_name": "TYPE_D",
      "operation": "MERGE",
      "merge_into": "TYPE_A"
    }
  ]
}
```

本地 Validator 在应用前检查：

- 顶层只能包含 `revisions`，且它必须是数组。
- 每个 Entry 的字段集合必须与其 operation 精确对应。
- 每个输入 Registry 名称必须被覆盖一次，不能遗漏、重复或增加未知名称。
- `REVISE.revised_edge_type` 必须满足原有四字段 Edge Type Schema。
- `MERGE.merge_into` 必须指向输入 Registry 中另一个真实名称。
- MERGE 目标自己的操作必须是 `KEEP` 或 `REVISE`，不能形成 Merge 链、指向删除项或指向自身。
- 应用 KEEP 和 REVISE 后得到的最终名称必须唯一。

应用算法不依赖 LLM 返回数组的顺序。程序先按 `original_name` 建立操作索引，再按原 Registry 顺序处理：KEEP 保留原对象、REVISE 放入新对象、DELETE 和 MERGE Source 不写入新 Registry。MERGE Target 会由自己的 KEEP 或 REVISE Entry 进入 Registry。最后再次执行完整 Registry Validator，成功后才替换正式 Registry。

如果用户直接输入 `END`，Feedback 为空。程序保存空的 `human_feedback.txt`，把 `feedback_applied` 记为 `false`，跳过 Registry Revision LLM，并让 Registry 原样进入下一批。

非空 Feedback Revision 成功后，Prompt 版本不变；新的 Registry 会成为下一批所有 Window 的 Registry 基线。

## Prompt 组成、变量和版本

模块加载并版本化九个 Prompt 文件。`manual_prompt` 交互仍只列出原有七个三阶段 Prompt 供人工修改；两个 Registry Revision Prompt 是固定 Prompt：

| 文件 | 用途 | 允许且必须存在的模板变量 |
| --- | --- | --- |
| `common/granularity_examples.txt` | 三阶段和 Registry Revision 共享的粒度规则与示例 | 无 |
| `discovery/system.txt` | Discovery System Prompt | 无 |
| `discovery/user.txt` | Discovery User Prompt | `{{context_window}}` |
| `comparison/system.txt` | Comparison System Prompt | 无 |
| `comparison/user.txt` | Comparison User Prompt | `{{candidate_edge_types}}`、`{{existing_registry}}` |
| `review/system.txt` | Review System Prompt | 无 |
| `review/user.txt` | Review User Prompt | `{{context_window}}`、`{{candidate_edge_types}}`、`{{comparison_results}}`、`{{existing_registry}}` |
| `registry_revision/system.txt` | Registry Revision System Prompt | 无 |
| `registry_revision/user.txt` | Registry Revision User Prompt | `{{human_feedback}}`、`{{existing_registry}}` |

每次调用的 System Message 按下面方式拼接：

```text
<当前阶段 system.txt>

<common/granularity_examples.txt>
```

User Message 只替换上表列出的双花括号变量。缺少变量、出现未知变量、文件缺失或内容为空都会拒绝运行。

首次运行时：

1. 读取并校验 `src/build_edges/prompts/` 下的九个文件。
2. 把完整快照保存为输出目录中的 `prompt_versions/v0001/`。
3. 第一批全部使用 `v0001`。

`manual_prompt` 模式每次人工批次检查按 Enter 后：

1. 重新读取源码目录中的九个 Prompt，其中终端列出的七个是三阶段可编辑 Prompt。
2. 重新执行完整文件和模板变量校验。
3. 校验失败时停留在当前检查点，提示修正后再次按 Enter。
4. 校验通过后保存下一个版本，如 `v0002`。
5. 即使文件内容没有变化，也保存新的版本快照，以记录下一批实际使用的 Prompt。

恢复运行时，程序先从输出目录的 `prompt_versions/{state.prompt_version}/` 加载历史版本，避免源码 Prompt 后续修改导致同一批次前后不一致。`manual_prompt` 只有跨过人工检查点后才读取源码 Prompt 并生成下一版本；`registry_feedback` 在反馈前后保持当前版本。

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

Window 的 Discovery、Comparison 或 Review 全部尝试失败后：

1. 保存该阶段的失败调用记录。
2. 把当前 Window `metadata.json` 标记为 `failed`，记录 `failed_stage` 和错误。
3. 把全局 `execution_state.json` 标记为 `failed`。
4. 终止整个运行，不继续后面的 Window。

Registry Revision 全部尝试失败后：

1. 保存 `registry_revision_request.json` 和失败的 `registry_revision_response.json`。
2. 保存 `registry_revision_error.json`。
3. 保持反馈前 Registry 不变。
4. 保留 `pending_feedback_stage: revising_registry` 并把全局状态标记为 `failed`。

修复网络、配置或 Prompt 问题后，可以用 `--resume` 从失败阶段继续。已经成功的 Window 阶段不会重新请求，已保存的人类 Feedback 也会直接复用。

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

当前实现不使用流式响应，也不打印每个成功阶段的“开始/完成”日志。成功请求进行期间，终端可以长时间没有任何新内容。每个 Window 完整提交后会打印 Discovery、Comparison、Review 数量及已有类型改名明细。

例如，20 个 Window 的三阶段发现会串行执行 60 个 DeepSeek 请求：

```text
20 Window × 3 stages = 60 requests
```

如果使用 `registry_feedback`，每个非最终完整批次的非空 Feedback 还会增加 1 次 Registry Revision 请求。20 个 Window、间隔 10 时，会在第 10 个 Window 后增加一次 Revision；第 20 个是最终批次，不再反馈。

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
  "feedback_mode": "registry_feedback",
  "pending_feedback_stage": null,
  "status": "running",
  "config": {
    "human_feedback_interval": 10,
    "feedback_mode": "registry_feedback",
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
| `feedback_mode` | 本次运行固定使用的人工反馈模式 |
| `pending_feedback_stage` | 尚未完成的 Registry Feedback 子阶段；普通 Window 处理时为 `null` |
| `status` | 全局执行状态 |
| `config` | 首次运行使用的配置副本 |

`next_stage` 的值：

| 值 | 含义 |
| --- | --- |
| `discovery` | 当前 Window 尚未成功完成 Discovery |
| `comparison` | Discovery 已保存，下一步是 Comparison |
| `review` | Discovery 和 Comparison 已保存，下一步是 Review |
| `commit` | 三次模型调用均已保存，下一步只需本地提交 Registry |

`pending_feedback_stage` 的值：

| 值 | 含义 |
| --- | --- |
| `null` | 当前没有待完成的 Registry Feedback |
| `collecting_feedback` | 正在终端收集多行自然语言 Feedback |
| `revising_registry` | Feedback 已保存，下一步调用或恢复 Registry Revision LLM |
| `applying_revision` | Revision Plan 已验证和保存，下一步在本地应用并提交 Registry |

全局 `status` 的值：

| 值 | 含义 |
| --- | --- |
| `running` | 正在本地处理、等待 DeepSeek，或上次被 Ctrl+C 中断时停留在运行态 |
| `waiting_for_enter` | `manual_prompt` 模式的一批完成，原终端正等待按 Enter |
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

## 每批人工反馈

达到 `human_feedback_interval` 且后面还有 Window 时，程序先保存当前 Registry 和 Batch Review Packet，再进入配置指定的反馈模式。终端都会显示：

- 已处理 Window 数。
- 本批新增 Edge Type 数。
- 当前 Registry 总数。
- 当前 Prompt 版本。
- `edge_type_registry.json` 路径。
- 本批 `review_packet.md` 路径。
- 当前 `feedback_mode`。

`manual_prompt` 会额外列出七个可修改的三阶段 Prompt。人工修改后回到原终端按 Enter，程序重新加载、校验并保存下一 Prompt 版本；Registry 保持不变。

`registry_feedback` 会提示输入多行自然语言意见并以单独一行 `END` 结束。非空内容会保存后调用 Registry Revision；空内容跳过 LLM 并保留 Registry。Revision 完成后终端打印反馈前后数量、四种操作统计以及 REVISE、MERGE、DELETE 简表。

只有后面仍有 Window 的完整批次才执行反馈。最后一批无论正好达到间隔还是不足间隔，都保存 Batch 结果后直接完成。例如 30 个 Window 只在第 10 和第 20 个后反馈，第 30 个后结束。

如果程序在反馈阶段关闭，使用 `--resume` 后根据 `pending_feedback_stage` 继续。已输入并保存的 Feedback、已验证的 Plan 和已完成的 Registry Commit 会分别复用，不要求从头重跑 Window。

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
│   │   ├── review/user.txt
│   │   ├── registry_revision/system.txt
│   │   └── registry_revision/user.txt
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
    │   ├── registry_after_windows.json
    │   ├── registry_after.json
    │   ├── newly_accepted_edge_types.json
    │   ├── batch_metadata.json
    │   ├── review_packet.md
    │   ├── human_feedback.txt
    │   ├── registry_revision_request.json
    │   ├── registry_revision_response.json
    │   ├── registry_revision_plan.json
    │   ├── registry_after_feedback.json
    │   └── registry_revision_error.json  # 只有 Revision 失败时存在
    └── batch_0002/
        └── ...
```

### `edge_type_registry.json`

当前完整 Registry，是 Edge Type Object 数组。首次运行从空数组开始。每个 Window Commit 后更新一次；Registry Feedback 成功应用后还会用 Revision 结果再次更新。

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

记录全局进度、批次、Prompt 版本、下一阶段、反馈模式、待处理反馈子阶段、状态和配置。每个成功阶段、每个 Window Commit、反馈子阶段切换以及进入或离开人工检查点时都会原子更新。

### `runs/<run_name>/metadata.json`

记录单个 Window 的事务状态，主要字段包括：

- 输入文件名、`trajectory_id`、`window_id` 和 `global_index`。
- 当前 Window 固定使用的 `prompt_version`。
- Window 开始时复制的完整 `registry_snapshot`。
- `completed_stages`。
- 最终 `accepted_edge_types`。
- `revised_existing_edge_types`：每项包含 `original_name`、完整 `original_edge_type` 和完整 `revised_edge_type`。
- `accepted_edge_type_count` 和 `revised_existing_edge_type_count`。
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

Review 的 `parsed_response` 同时保存 `accepted_edge_types` 和 `revised_existing_edge_types` 两个完整数组。这些文件用于审计实际 Prompt、模型原始返回和本地校验结果。文件可能较大，因为 `raw_response` 和实际消息会完整保留；已识别的凭证会被 Redactor 替换。

### `batches/batch_NNNN/`

- `registry_before.json`：本批开始前的 Registry。
- `registry_after_windows.json`：本批全部 Window 提交后、Human Feedback 应用前的 Registry，也是 Revision LLM 的实际输入。
- `registry_after.json`：为兼容原有 `manual_prompt` 输出保留的 `registry_after_windows.json` 同内容别名。
- `newly_accepted_edge_types.json`：从本批各 Window 的 Review 元数据汇总的新增类型；已有类型改名不会计入新增。
- `batch_metadata.json`：批次范围、Prompt 版本、新增和已有类型修订次数、反馈模式、是否要求/完成/应用反馈、操作统计和保存时间。
- `review_packet.md`：便于人工阅读的批次信息、新增类型、本批已有类型修订前后完整定义及当前完整 Registry。同一已有类型在不同 Window 中分别修订会计为多次。
- `human_feedback.txt`：终端输入并去掉首尾空白后的原始多行 Feedback；空反馈时是空文件。
- `registry_revision_request.json`：实际 System/User Message、Prompt 版本、模型和请求设置。
- `registry_revision_response.json`：所有 attempts、Provider 原始响应、解析结果、错误和历史失败调用。
- `registry_revision_plan.json`：通过完整 Validator 的 Revision Plan。
- `registry_after_feedback.json`：应用 Revision Plan 后的 Registry；空反馈和 `manual_prompt` 时与反馈前 Registry 相同。
- `registry_revision_error.json`：Revision 调用、解析、校验或应用失败时的错误和保存时间。

空 Feedback 会跳过 Revision LLM，因此不会生成 Revision request、response 和 plan 文件。最终批次不执行反馈，因此只包含批次基础文件。

## 断点恢复保证

恢复命令不会简单地从头重跑，而是按已经落盘的事务状态继续：

1. 校验当前输入 manifest 与首次运行完全一致。
2. 校验当前 config 与首次运行完全一致。
3. 按 Window 顺序，以每份 `metadata.json` 的 Registry 快照为基准，先重放已有类型修订，再追加接受的新类型；校验修订前定义和更新后大小。
4. 每到一个 `feedback_completed: true` 的批次边界，先校验重建值等于 `registry_after_windows.json`，再用 `registry_after_feedback.json` 替换当前重建值。
5. 重建结果会覆盖 `edge_type_registry.json`，修正 Registry 已写但全局状态尚未推进等中断情况。
6. 从 `prompt_versions/{prompt_version}` 加载历史 Prompt。
7. 根据 `next_window_index` 和 `next_stage` 恢复 Window 阶段。
8. 根据 `pending_feedback_stage` 恢复 Feedback 收集、Revision 调用或 Plan 应用。
9. 从对应 response/plan 文件读取并重新校验已经完成的结果。

如果状态是：

- `failed`：先改回运行态，再从保存的 Window 阶段或 Registry Revision 子阶段重试。
- `waiting_for_enter`：先恢复人工 Prompt 检查流程。
- `completed`：打印已经完成并直接返回，不重复请求。
- `running`：按最后保存的 Window 和阶段继续，适用于 Ctrl+C 或进程异常退出。

Registry 以每个已提交 Window 的新增与修订记录，以及每个已完成反馈批次的 `registry_after_feedback.json` 为共同事实来源。这样逐 Window 改名和批次级 DELETE、REVISE、MERGE 在恢复时都会保留。重建时若发现 Window 未完整提交、快照或修订前定义不一致、反馈前 Registry 不一致、结构错误或当前 Registry 内名称重复，会拒绝继续。

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

检查九个文件是否都存在且非空，并确保 User Prompt 精确保留各自要求的 `{{...}}` 变量。System Prompt 和公共 Prompt 不能增加模板变量。

### Comparison 一直重试

查看 `comparison_response.json` 中每个 attempt 的 `error`。常见原因是候选没有全部分类、同一候选出现在多个分类、匹配了不存在的 Registry 名称，或者 Registry 为空时没有把全部候选放进 `new`。

### Review 一直重试

查看 Review attempt 的本地校验错误。常见原因是输出包含多余字段、Edge Type 名称格式错误、接受列表内部重名，或者修订与新增应用后 Registry 出现重名。已有类型在本轮改名后，新增类型可以使用它让出的原名称。

### Registry Revision 一直重试

查看当前批次的 `registry_revision_response.json`。常见原因是 Plan 没有恰好覆盖完整 Registry、同一个原始名称出现多次、operation 带有错误字段、MERGE 指向 DELETE/MERGE 项，或者 REVISE 后产生重复名称。全部重试失败时使用同一输出目录执行 `--resume`，程序会复用已经保存的 `human_feedback.txt`。

### 输入 Feedback 后没有调用模型

单独输入 `END` 表示空 Feedback。程序会有意跳过 Revision LLM，把 `feedback_applied` 保存为 `false` 并保留当前 Registry。

### `--resume` 提示输入发生变化

恢复要求输入目录绝对路径、文件集合、顺序和每个文件的 SHA-256 全部一致。恢复期间不要重新执行会覆盖 `split_windows` 的上游步骤。

### `--resume` 提示 Config 不一致

使用首次运行时相同的 `human_feedback_interval`、`feedback_mode` 和 `max_llm_retries`。如果需要改变配置，应新建输出目录重新开始一轮。

### 终端停在批次边界

当本批达到 `human_feedback_interval` 且后面还有 Window 时，程序会等待人工反馈。查看终端给出的 Registry 和 Review Packet：`manual_prompt` 模式下按需修改 Prompt 后，在原终端按 Enter；`registry_feedback` 模式下输入多行意见，以单独一行 `END` 结束。最后一批不会等待反馈；若没有出现反馈提示，请结合 `execution_state.json` 判断是否仍在等待模型响应。

### 终端无输出但进程仍在

先读取 `execution_state.json`，再查看最近阶段文件和 Python 进程。请求阶段最长可以等待 600 秒，且成功请求期间默认不打印进度。

## 临时验证文件

模块的临时验证代码和数据位于仓库 `temp/build_edges_tests/`，由 `.gitignore` 排除，不属于正式模块源码。
