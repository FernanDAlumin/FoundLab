# FoundLab

> 一个 dashboard-first 的投资决策复盘回测实验室：把真实决策和干净、可重复的基准策略放在一起比较。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Status](https://img.shields.io/badge/status-Phase%201%20foundation-orange)

[English README](README.md)

FoundLab 想回答的是一个问题：

> “我当时那笔操作，真的比一个简单基准更好吗？”

它不是用来预测未来的水晶球，而是用同一套历史数据、执行规则和费用假设，把过去的投资动作重新放回跑道上，和日定投、再平衡或其他基准策略认真比一比。

## 为什么是 FoundLab？

- **复盘决策，而不是复盘情绪** - 把真实历史动作和标准基准策略放到同一张桌子上。
- **Dashboard first** - 长期体验围绕 run、warning、report 和多策略对比展开。
- **数据源解耦** - provider 被收在清晰契约后面，不让策略逻辑直接粘上 SDK。
- **适合 agent 操作** - 项目自带本地 workflow skill，方便复用现有 Python 基础设施做研究运行。
- **面向中国市场数据** - 当前数据准备已支持 AkShare 的 ETF、A 股股票和公募基金日频数据。

## 当前状态

FoundLab 目前处在 **Phase 1: foundation**。项目已经搭好后端、数据层、存储层、worker 和 React dashboard 外壳；当前重点是准备归一化行情数据，并记录可追溯的研究运行。

已经可用：

- [x] Python 包结构、严格类型检查和 lint 配置。
- [x] provider-neutral 的行情数据契约。
- [x] AkShare 数据源边界。
- [x] ETF、A 股股票、公募基金的日频数据归一化。
- [x] SQLite 元数据和行情数据存储。
- [x] 资产与运行记录的 FastAPI 接口。
- [x] 同步 worker 数据准备任务。
- [x] React/Vite dashboard 外壳。
- [x] 项目本地 agent workflow skill。

正在路上：

- [ ] 完整回测执行引擎。
- [ ] CSV 历史决策回放。
- [ ] 手续费和税费模型。
- [ ] 收益、回撤、波动率、交易次数等指标。
- [ ] HTML、Markdown、PNG、CSV 等静态报告产物。
- [ ] run 历史、报告查看和多运行对比等 dashboard 视图。

## 快速开始

### 后端

```bash
uv sync --extra dev
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

### 前端

```bash
npm --prefix frontend install
npm --prefix frontend test
npm --prefix frontend run build
```

启动 dashboard：

```bash
npm --prefix frontend run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

## Agent Workflow

FoundLab 在 `skill/foundlab-agent-workflow/` 内置了项目本地 skill。适合在你希望 agent 直接操作 FoundLab 时使用：拉取 AkShare 数据、准备归一化日频行情、运行定投对比，并返回经过验证的结果。

示例请求：

```text
Use $foundlab-agent-workflow to download 019058 public fund data from 2026-01-01
to 2026-04-30 and compare daily, weekly, and monthly fixed investment with
12 CNY per valid NAV day.
```

这个 workflow 会优先复用现有 provider、worker 和 storage 层；研究数据会通过普通 FoundLab run 存储，而不是散落成临时文件。

## API 一眼看

创建资产：

```bash
curl -X POST http://127.0.0.1:8000/api/assets \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"510300","asset_type":"etf","name":"沪深300ETF"}'
```

创建数据准备运行：

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

触发数据准备并查询运行记录：

```bash
curl -X POST http://127.0.0.1:8000/api/runs/1/prepare-data
curl http://127.0.0.1:8000/api/runs/1
```

## 项目地图

```text
.
├── src/foundlab/
│   ├── api/              # FastAPI 应用、schema、资产路由、运行路由
│   ├── core/             # 枚举、模型、provider 协议、归一化逻辑
│   ├── storage/          # SQLModel 表、数据库会话、仓储函数
│   └── worker/           # 同步任务和数据准备入口
├── frontend/             # Vite + React dashboard
├── tests/                # 后端、API、存储、worker 和数据测试
├── docs/superpowers/     # 设计文档和阶段实现计划
└── skill/                # FoundLab agent workflow skill
```

## 架构

FoundLab 当前采用模块化单体结构。`foundlab.core` 保存与框架无关的核心契约和数据处理逻辑；API、worker 和 storage 依赖 core，而 core 不依赖 Web 层或数据库层。

当前数据流：

1. API 或 agent 创建资产和运行记录。
2. worker 根据 run 配置构造 `ProviderRequest`。
3. `AkShareProvider` 拉取 ETF、A 股股票或公募基金日频数据。
4. 归一化逻辑生成 `NormalizedBar`。
5. storage 保存原始 provider 行、清洗后的日频行情和数据警告。
6. run 状态更新为 `succeeded`、`succeeded_with_warnings` 或 `failed`。

## 开发约定

- 常规测试使用 fixture 或 fake client，不依赖实时 AkShare 网络访问。
- live AkShare 调用更适合作为人工 smoke test 或 agent research run。
- 新增数据源时，实现 `MarketDataProvider`，不要让业务逻辑直接调用 provider SDK。
- 新增策略时，先生成中立的 `OrderIntent`，再让执行层统一处理成交、非交易日、现金约束和费用。
- 报告和 dashboard 应清楚展示数据源、取数时间、清洗假设、执行规则、费用假设和 warning 数量。

## Roadmap

- ETF 日定投基准策略。
- CSV 历史决策回放。
- gross/net 双账本和基础费用模型。
- 总收益、年化收益、最大回撤、波动率、交易次数等指标。
- A 股股票和公募基金更细的清洗 warning 与执行规则。
- 静态报告导出。
- dashboard 中的 run 历史、报告查看和多运行对比。

## 贡献

FoundLab 还很早期，所以有价值的边界也很清楚。欢迎小而准的贡献：数据源改进、聚焦测试、更清晰的文档，以及能让 run 更容易被检查的 dashboard 视图。

如果要做较大的改动，建议先开 issue 或写清楚变更边界：数据契约、策略执行、报告生成和 dashboard UX 在设计上是刻意分开的。

## 许可证

FoundLab 基于 [MIT License](LICENSE) 发布。
