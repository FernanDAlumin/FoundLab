# FoundLab

[English README](README.md)

FoundLab 是一个面向投资决策复盘的仪表盘优先回测平台。它用于把历史投资动作与标准基准策略放在同一套数据、执行规则和费用假设下比较，帮助回答“当时的决策相对定投、再平衡或其他基准到底好在哪里、差在哪里”。

## 当前状态

项目目前处在 Phase 1 基础设施阶段，已经搭好后端、数据层、存储层、worker 和前端仪表盘骨架。当前可用的重点是数据准备和运行记录管理；完整策略执行、CSV 决策回放、指标计算和静态报告生成还属于后续阶段。

已实现能力包括：

- Python 包结构和类型检查配置。
- provider-neutral 的核心数据契约。
- AkShare 数据源边界。
- ETF、A 股股票、公募基金的日频数据归一化。
- SQLite 元数据存储，包括资产、回测运行、原始行情、清洗行情和数据警告。
- 最小 FastAPI 服务。
- 同步 worker 骨架和数据准备任务。
- 最小 React/Vite 仪表盘外壳。
- 项目本地 agent workflow skill，用于让 agent 复用现有 Python 基础设施完成数据准备和定投对比研究。

暂未实现：

- 完整回测执行引擎。
- CSV 历史决策回放。
- 手续费和税费模型。
- 收益、回撤、波动率等指标计算。
- HTML、Markdown、PNG、CSV 等静态报告产物生成。
- 丰富的仪表盘交互和运行对比视图。

## 技术栈

- 后端：Python 3.11+、FastAPI、SQLModel、SQLite、pandas、AkShare。
- 任务执行：当前为同步 worker，后续可替换或扩展为队列式后台任务。
- 前端：React 19、Vite、TypeScript、Vitest、lucide-react。
- 工具链：uv、pytest、ruff、mypy、npm。

## 项目结构

```text
.
├── src/foundlab/
│   ├── api/              # FastAPI 应用、请求响应 schema、资产和运行路由
│   ├── core/             # 核心枚举、数据契约、数据源协议、归一化逻辑
│   ├── storage/          # SQLite/SQLModel 表模型、数据库会话、仓储函数
│   └── worker/           # 同步任务入口和数据准备 job
├── frontend/             # Vite React 仪表盘
├── tests/                # 后端单元测试、API 测试、worker 测试
├── docs/superpowers/     # 设计文档和阶段实现计划
├── skill/                # FoundLab 本地 agent workflow skill
└── foundlab.db           # 本地 SQLite 数据库
```

## 后端快速开始

安装依赖：

```bash
uv sync --extra dev
```

运行测试和静态检查：

```bash
uv run pytest -q
uv run ruff check .
uv run mypy src
```

启动 API：

```bash
uv run uvicorn foundlab.api.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok","service":"foundlab-api"}
```

## 前端快速开始

安装依赖：

```bash
npm --prefix frontend install
```

运行测试和构建：

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

启动仪表盘：

```bash
npm --prefix frontend run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

## API 示例

创建资产：

```bash
curl -X POST http://127.0.0.1:8000/api/assets \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"510300","asset_type":"etf","name":"沪深300ETF"}'
```

创建运行记录：

```bash
curl -X POST http://127.0.0.1:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name":"510300 data prepare",
    "asset_ids":["510300"],
    "strategy_name":"data_prepare",
    "start_date":"2024-01-02",
    "end_date":"2024-01-05",
    "adjustment":"qfq"
  }'
```

触发数据准备：

```bash
curl -X POST http://127.0.0.1:8000/api/runs/1/prepare-data
```

查询运行记录：

```bash
curl http://127.0.0.1:8000/api/runs/1
```

## Agent 工作流

当你希望让 agent 直接操作 FoundLab 做研究运行时，可以使用项目内置 skill：

```text
Use $foundlab-agent-workflow to download 019058 public fund data from 2026-01-01
to 2026-04-30 and compare daily, weekly, and monthly fixed investment with
12 CNY per valid NAV day.
```

这个 workflow 会优先复用现有的 provider、worker 和 storage 层，按普通 FoundLab run 存储数据，并基于清洗后的行情计算结果。公募基金默认使用 `AssetType.PUBLIC_FUND` 和 `AdjustmentMode.NONE`，除非请求里另有说明。

## 核心设计边界

FoundLab 采用模块化单体结构。`foundlab.core` 保存与框架无关的核心契约和数据处理逻辑；API、worker 和 storage 依赖 core，但 core 不依赖 Web 层或数据库层。这样可以让回测核心保持可测试、可复用，并为后续 CLI、notebook 或更完整的后台任务系统保留空间。

当前数据流是：

1. API 或 agent 创建资产和运行记录。
2. worker 根据 run 配置构造 `ProviderRequest`。
3. `AkShareProvider` 拉取 ETF、股票或公募基金日频数据。
4. 归一化逻辑生成 `NormalizedBar`。
5. storage 同时保存原始 provider 行、清洗后的日频行情和数据警告。
6. run 状态更新为 `succeeded`、`succeeded_with_warnings` 或 `failed`。

## 数据与数据库

默认数据库为项目根目录下的 SQLite 文件：

```text
foundlab.db
```

表结构由 FastAPI lifespan 或显式调用 `create_db_and_tables()` 创建。当前仓储层支持：

- 创建和列出资产。
- 创建和查询 backtest run。
- 更新 run 状态。
- 替换指定 run 的原始行情、清洗行情和数据警告。
- 读取原始行情、清洗行情和警告记录。

## 开发约定

- 常规测试不依赖实时 AkShare 网络访问，优先使用 fixture 或 fake client。
- live AkShare 调用适合作为人工 smoke test 或 agent research run。
- 新增数据源时，应实现 `MarketDataProvider` 协议，而不是让业务逻辑直接调用 provider SDK。
- 新增策略时，应先生成中立的 `OrderIntent`，再由执行层统一处理成交、非交易日、现金约束和费用。
- 报告和仪表盘应清楚展示数据源、取数时间、清洗假设、执行规则、费用假设和 warning 数量。

## 路线图

近期后续阶段预计包括：

- ETF 路径的日定投基准策略。
- CSV 历史决策回放。
- gross/net 双账本和基础费用模型。
- 总收益、年化收益、最大回撤、波动率、交易次数等指标。
- A 股股票和公募基金更细的清洗警告与执行规则。
- HTML/Markdown/PNG/CSV 静态报告产物。
- 仪表盘中的 run 历史、报告查看和多运行对比。

## 许可证

见 [LICENSE](LICENSE)。
