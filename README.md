# llm_Iterative_Edge_Type

本仓库从原始 Agent Trajectory 中依次完成轨迹规范化、Context Window 切分和语义 Edge Type 发现。

根目录的 `run.py` 是完整批处理入口，一次运行固定执行三个阶段：

```text
trajectory/*/agent/trajectory.json
                │
                ▼
        1. Preprocess
                │
                ▼
       processed_trajectory/
                │
                ▼
           2. Split
                │
                ▼
          split_windows/
                │
                ▼
       3. Build Edges
                │
                ▼
           build_edges/
```

## 环境要求

- Python 3.10+
- 无第三方 Python 包依赖
- 可用的 DeepSeek API Key

三个阶段都会根据数据情况调用 DeepSeek。

## DeepSeek 配置

在 `src/.env` 中配置：

```dotenv
DEEPSEEK_API_KEY=你的APIKey
DEEPSEEK_MODEL=deepseek-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

规则：

- `DEEPSEEK_API_KEY` 必填。
- `DEEPSEEK_MODEL` 未配置时默认使用 `deepseek-flash`。
- `DEEPSEEK_BASE_URL` 未配置时默认使用 `https://api.deepseek.com`。
- 系统环境变量优先；`src/.env` 不覆盖已经存在的同名环境变量。
- `.env` 支持空行、注释、`KEY=VALUE`、单行引号值和可选的 `export` 前缀。
- `.env` 不执行变量插值。
- 程序只读取 `src/.env`，不会修改它。

如果没有配置 API Key，入口在创建本次运行目录之前退出。

## 运行完整三阶段流程

在仓库根目录执行：

```powershell
python run.py
```

所有输入、配置和输出路径都以 `run.py` 所在的仓库根目录为基准，因此从其他工作目录启动也可以正常定位文件。

入口不接收命令行参数。输入固定来自：

```text
trajectory/*/agent/trajectory.json
```

如果没有匹配的输入文件，程序直接退出且不创建运行目录。

## 第一阶段：Preprocess

入口按完整输入路径排序，依次读取：

```text
trajectory/<案例文件夹>/agent/trajectory.json
```

每个成功处理的轨迹保存为：

```text
processed_trajectory/trajectory1.json
processed_trajectory/trajectory2.json
...
```

编号取决于排序后的输入顺序。即使某个案例失败，后续案例仍使用原来的枚举编号，因此输出编号可能不连续。

每份规范化轨迹顶层都会新增：

```json
{
  "metadata": {
    "source_trajectory": "trajectory/<案例文件夹>/agent/trajectory.json"
  }
}
```

`source_trajectory` 使用相对于仓库根目录的 `/` 分隔路径，用于从处理结果追踪原始轨迹。

预处理阶段：

- 保留并规范化 Agent Trajectory 的有效内容。
- 在需要拆分未标识的聚合 observation 时调用 DeepSeek。
- 单个案例失败时记录错误并继续处理其余案例。
- 每处理完一个案例就更新一次本次运行的 `summary.json`。

详细规则见 [Preprocess README](src/preprocess/README.md)。

## 第二阶段：Split

Preprocess 循环结束后，入口读取本次运行中所有成功生成的：

```text
processed_trajectory/*.json
```

Split 使用：

```text
src/split/config.yaml
```

配置控制：

- Previous Summary 最大 Token 数。
- Future Summary 最大 Token 数。
- 单个 Window 最大 Token 数。
- 单个 Window 最大事件数。
- 相邻 Window 的重叠事件数。

Split 会切分事件，并调用 DeepSeek 为每个 Window 生成前文与后文摘要。输出形式为：

```text
split_windows/trajectory1__window_0001.json
split_windows/trajectory1__window_0002.json
split_windows/trajectory2__window_0001.json
...
```

空轨迹不会生成 Window，并计入 `empty_trajectories`。单个轨迹或 Window 失败时继续处理其他输入，同时增加 Split 失败计数。

详细规则见 [Split README](src/split/README.md)。

## 第三阶段：Build Edges

Split 结束后，根入口调用 `src.build_edges.main`，参数等价于：

```powershell
python -m src.build_edges `
  --input-dir ./runs/MM-DD_序号/split_windows `
  --output-dir ./runs/MM-DD_序号/build_edges `
  --config ./src/build_edges/config.yaml
```

根入口不会预先创建 `build_edges/`。Build Edges 在确认输入合法后自行初始化输出目录和执行状态。

Build Edges 按 `trajectory_id` 和 `window_index` 排序处理 Window。每个 Window 串行执行三次 LLM 调用：

1. **Blind Discovery**：从当前 Window 独立发现候选 Edge Type。
2. **Type Comparison**：把候选类型与当前 Registry 快照比较。
3. **Type Review**：结合 Window、候选、比较结果和 Registry，决定接受哪些新类型。

Review 接受并通过严格 JSON 校验的类型会追加到：

```text
build_edges/edge_type_registry.json
```

Build Edges 使用：

```text
src/build_edges/config.yaml
```

默认配置为：

```yaml
human_feedback_interval: 10
max_llm_retries: 3
```

含义：

- 每完成 10 个 Window，保存批次结果并进入人工 Prompt 检查点。
- 单个 LLM 阶段首次失败后最多额外重试 3 次，即同一阶段最多请求 4 次。

到达人工检查点后，程序会在原终端等待 Enter。此时可以查看：

```text
build_edges/batches/batch_NNNN/review_packet.md
build_edges/edge_type_registry.json
```

并按需修改：

```text
src/build_edges/prompts/
```

按 Enter 后，程序重新校验 Prompt、保存下一版本快照并继续下一批。最后一批处理完后直接结束，不再等待 Enter。

Build Edges 使用非流式 DeepSeek 请求，成功调用开始和结束时默认不打印逐阶段日志。因此终端可能在请求期间长时间没有新输出。20 个 Window 正常需要串行完成 60 次阶段调用。

完整输入契约、三阶段 Schema、Prompt 版本、审计文件和恢复规则见 [Build Edges README](src/build_edges/README.md)。

## 每次运行的目录命名

每次执行 `python run.py` 都会创建一个新的运行目录：

```text
runs/MM-DD_序号/
```

例如，同一天连续运行三次会创建：

```text
runs/09-22_1/
runs/09-22_2/
runs/09-22_3/
```

日期只包含月和日，不包含年份。序号从 1 开始，使用当天现有目录中的最大序号加 1。程序不会覆盖以前的运行结果。

## 完整输出结构

一次正常完成的运行目录如下：

```text
runs/
└── MM-DD_1/
    ├── summary.json
    ├── preprocess_calls.jsonl
    ├── checkpoint.json
    ├── cache/
    ├── processed_trajectory/
    │   ├── trajectory1.json
    │   ├── trajectory2.json
    │   └── ...
    ├── split_windows/
    │   ├── trajectory1__window_0001.json
    │   ├── trajectory1__window_0002.json
    │   ├── trajectory2__window_0001.json
    │   └── ...
    └── build_edges/
        ├── edge_type_registry.json
        ├── execution_state.json
        ├── window_manifest.json
        ├── prompt_versions/
        │   ├── v0001/
        │   └── v0002/
        ├── runs/
        │   ├── trajectory1__window_0001/
        │   │   ├── metadata.json
        │   │   ├── discovery_request.json
        │   │   ├── discovery_response.json
        │   │   ├── comparison_request.json
        │   │   ├── comparison_response.json
        │   │   ├── review_request.json
        │   │   └── review_response.json
        │   └── ...
        └── batches/
            ├── batch_0001/
            │   ├── registry_before.json
            │   ├── registry_after.json
            │   ├── newly_accepted_edge_types.json
            │   ├── batch_metadata.json
            │   └── review_packet.md
            └── ...
```

部分预处理辅助文件只在相关调用实际发生时生成，因此具体运行目录中可能没有 `preprocess_calls.jsonl`、`checkpoint.json` 或 `cache/`。

## `summary.json`

根入口持续更新 `summary.json`。结构示例：

```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "cases": [
    {
      "case": "案例文件夹名称",
      "input": "trajectory/案例文件夹名称/agent/trajectory.json",
      "status": "succeeded",
      "output": "processed_trajectory/trajectory1.json"
    }
  ],
  "split": {
    "output": "split_windows",
    "windows": 20,
    "empty_trajectories": 0,
    "failed": 0
  },
  "build_edges": {
    "output": "build_edges",
    "status": "succeeded",
    "exit_code": 0
  }
}
```

Build Edges 开始前先写入：

```json
{
  "status": "running",
  "exit_code": null
}
```

阶段正常结束后更新为 `succeeded` 和退出码 `0`。如果 Build Edges 返回非零退出码，则更新为 `failed`。如果根进程在 Build Edges 运行期间被 Ctrl+C 或直接关闭，外层 `summary.json` 可能保留 `running`；应以 `build_edges/execution_state.json` 为准判断内部准确进度。

## 失败处理和最终退出码

### Preprocess 失败

单个案例失败后继续处理剩余案例。失败信息经过凭证隐藏后写入该案例的 summary 记录。

### Split 失败

单个输入或 Window 失败时由 Split 累计失败数并继续。Split 整体抛出异常时，根入口记录错误并仍然进入第三阶段；如果没有生成任何合法 Window，Build Edges 会返回失败。

### Build Edges 失败

Build Edges 会保存最后成功的 Window、阶段、Registry 和失败调用记录，然后返回非零退出码。根入口把第三阶段标记为 `failed`。

### 根入口退出码

满足以下任意条件时，`run.py` 最终退出码为 `1`：

- 至少一个 Preprocess 案例失败。
- Split 失败计数不为 0。
- Build Edges 退出码不为 0。

只有三个阶段都没有失败时，最终退出码才是 `0`。

## 恢复第三阶段

根入口每次启动都会创建新的 `MM-DD_序号` 目录，不会自动寻找并恢复旧运行。如果某次运行只在 Build Edges 阶段中断或失败，不要重新执行 `python run.py` 来恢复该目录。

使用原运行目录单独恢复：

```powershell
python -m src.build_edges `
  --input-dir ./runs/09-22_2/split_windows `
  --output-dir ./runs/09-22_2/build_edges `
  --config ./src/build_edges/config.yaml `
  --resume
```

恢复前确保原 Build Edges Python 进程已经退出。不要让两个进程同时写同一个 `build_edges/`。

直接恢复 Build Edges 不会自动修改外层 `summary.json` 的 `build_edges.status`；内部真实状态记录在：

```text
runs/09-22_2/build_edges/execution_state.json
```

## 单独运行各模块

三个模块仍可独立调用：

- Preprocess：[src/preprocess/README.md](src/preprocess/README.md)
- Split：[src/split/README.md](src/split/README.md)
- Build Edges：[src/build_edges/README.md](src/build_edges/README.md)

根入口自动加载 `src/.env`。原有的 `python -m src.preprocess`、`python -m src.split.main` 和 `python -m src.build_edges` 独立入口保持可用。
