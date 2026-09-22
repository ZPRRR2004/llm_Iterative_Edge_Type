# Split Module

本模块将一个文件夹中的预处理 Agent Trajectory JSON 批量切分为独立 Window，
并为每个 Window 生成一句前文摘要和一句后文摘要。它不负责发现边类型、连边或维护关系类型库。

## 运行

在仓库根目录运行：

```powershell
python -m src.split `
  --input-dir ./runs/03-22_1/processed_trajectory `
  --output-dir ./runs/03-22_1/split_windows
```

也可以直接运行：

```powershell
python src/split/main.py --input-dir ./input --output-dir ./output
```

程序读取 `src/.env` 中的 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL` 和
`DEEPSEEK_BASE_URL`；已存在的系统环境变量优先。输入目录和输出目录只通过命令行指定。

默认配置位于 `config.yaml`，只包含以下五项：

```yaml
max_previous_summary_tokens: 100
max_future_summary_tokens: 100
max_window_tokens: 6000
max_window_events: 5
overlap_events: 1
```

可以使用 `--config` 指定另一份配置文件。配置加载器只接受这五个整数配置项。

## 切分规则

- 输入文件按文件名排序，每条轨迹的 `events` 保持原始数组顺序。
- Event 是不可拆分单位；Core 使用 Token 上限和 Event 数量上限进行贪心切分。
- 单个超长 Event 仍完整进入一个 Core，并在元数据中标记 `oversized: true`。
- Overlap 取当前 Core 之前最近的完整 Events，不占 Core 预算。
- Previous Events 截止到 Overlap 之前；Future Events 从 Core 之后开始。
- 空轨迹不产生 Window；格式错误的轨迹会报告错误并继续处理其他输入。

`token_counter.py` **只按紧凑 JSON 的字符数粗略估算 Token**，换算公式为
`ceil(字符数 / 4)`。这个值用于确定性切分和摘要长度复核，不等同于模型 tokenizer 的精确结果；
中文、代码和特殊符号较多时可能有明显误差。

## 输出

所有 Window 直接保存在同一个输出文件夹中：

```text
trajectory1__window_0001.json
trajectory1__window_0002.json
trajectory2__window_0001.json
```

每个文件依次包含 `user_query`、`previous_summary`、完整 `overlap` Events、
完整 `core` Events 和 `future_summary`。元数据包含源文件、源路径、原始数组下标、
Core Event 数、估算 Token 数和超长标记。

第一个 Window 的 Previous Events 为空时不调用摘要模型；最后一个 Window 的 Future Events
为空时也不调用。单 Window 轨迹不会调用摘要模型。摘要必须为单行、非列表格式，且字符估算
不超过配置上限；输出截断或校验失败时使用 `prompts/retry.txt` 最多再重试两次，
不会直接裁剪摘要字符串。模型请求统一使用共享的 `src/deepseek_client.py`。

输出 JSON 使用临时文件完成写入后再原子替换。同一输出目录中如果存在当前轨迹不再需要的旧
Window，程序会拒绝继续处理该轨迹，避免混入不同切分配置的遗留结果。
