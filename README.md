# llm_Iterative_Edge_Type

## 批量预处理

在 `src/.env` 中配置 DeepSeek（也支持系统环境变量，系统环境变量优先）：

```dotenv
DEEPSEEK_API_KEY=你的APIKey
DEEPSEEK_MODEL=deepseek-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

在仓库根目录运行：

```powershell
python run.py
```

入口加载 `src/.env`，按名称顺序处理 `trajectory/*/agent/trajectory.json`。
支持 Python 3.10+，无需第三方依赖；实际预处理会调用 DeepSeek。
所有目录均相对于 `run.py` 所在位置，因此从其他工作目录启动也可使用。
`.env` 支持空行、注释、`KEY=VALUE`、单行引号值和可选的 `export` 前缀，
不进行变量插值。现有 `src/.env` 内容不会被入口修改。

每次运行创建一个新目录，名称为本地月日加当天递增序号（从 1 开始）：

```text
runs/
└── MM-DD_1/
    ├── summary.json
    ├── preprocess_calls.jsonl
    ├── checkpoint.json
    ├── cache/
    └── processed_trajectory/
        ├── trajectory1.json
        ├── trajectory2.json
        └── ...
```

输入轨迹按案例文件夹名称排序，依次保存为 `trajectory1.json`、`trajectory2.json` 等。
每个输出 JSON 的顶层 `metadata.source_trajectory` 记录原轨迹相对于仓库根目录的路径。
程序不改动输入文件，也不覆盖以前的运行结果。某个案例失败时继续处理剩余案例；
`summary.json` 汇总成功、失败及结果位置。有失败时入口退出码为 1，全部成功为 0。
如果没有匹配的输入或没有配置 API Key，则不创建运行目录。

单文件接口见 [预处理说明](src/preprocess/README.md)。根目录 `run.py` 自动加载
`src/.env`；原有单文件入口 `python -m src.preprocess` 继续使用环境变量。
