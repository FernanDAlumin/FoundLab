# FoundLab

> A dashboard-first backtesting lab for reviewing investment decisions against clean, repeatable baselines.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Status](https://img.shields.io/badge/status-Phase%201%20foundation-orange)

[中文 README](README.zh.md)

FoundLab helps you answer a practical investing question:

> "Was that decision actually better than a simple baseline?"

It is not built to predict the future. It is built to replay the past with the same data,
execution rules, and assumptions so decisions can be compared with daily investing,
rebalancing, and other baseline strategies.

## Why FoundLab?

- **Decision review, not vibes** - compare real historical actions with baseline strategies.
- **Dashboard first** - the long-term interface is built around inspecting runs, warnings, and reports.
- **Provider-neutral core** - data providers stay behind a clean contract instead of leaking into strategy logic.
- **Agent-friendly workflow** - the repo includes a project-local skill for repeatable research runs.
- **China market data ready** - current data preparation supports AkShare ETF, A-share stock, and public fund daily data.

## Current Status

FoundLab is in **Phase 1: foundation**. The project already has the backend, storage, data
pipeline, worker skeleton, and React dashboard shell needed to prepare normalized market data
and track research runs.

What works today:

- [x] Python package scaffold with strict typing and linting.
- [x] Provider-neutral market data contracts.
- [x] AkShare provider boundary.
- [x] Daily ETF, stock, and public fund normalization.
- [x] SQLite metadata and market data storage.
- [x] FastAPI endpoints for assets and runs.
- [x] Synchronous worker job for data preparation.
- [x] React/Vite dashboard shell.
- [x] Project-local agent workflow skill for research runs.

Coming next:

- [ ] Full backtesting execution engine.
- [ ] CSV decision replay.
- [ ] Fee and tax models.
- [ ] Metrics such as return, drawdown, volatility, and trade count.
- [ ] Static report artifacts in HTML, Markdown, PNG, and CSV.
- [ ] Rich dashboard views for run history, reports, and comparisons.

## Quick Start

### Backend

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy src
```

Start the API:

```bash
uv run uvicorn foundlab.api.main:app --reload
```

Check that it is alive:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"foundlab-api"}
```

### Frontend

```bash
npm --prefix frontend install
npm --prefix frontend test
npm --prefix frontend run build
```

Start the dashboard:

```bash
npm --prefix frontend run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Agent Workflow

FoundLab ships with a project-local skill at `skill/foundlab-agent-workflow/`. Use it when
you want an agent to operate the existing Python infrastructure directly: fetch AkShare data,
prepare normalized daily bars, run fixed-investment comparisons, and report verified results.

Example request:

```text
Use $foundlab-agent-workflow to download 019058 public fund data from 2026-01-01
to 2026-04-30 and compare daily, weekly, and monthly fixed investment with
12 CNY per valid NAV day.
```

The workflow prefers existing provider, worker, and storage layers before adding new framework
code. Research data is stored through normal FoundLab runs instead of one-off files.

## API Sneak Peek

Create an asset:

```bash
curl -X POST http://127.0.0.1:8000/api/assets \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"510300","asset_type":"etf","name":"CSI 300 ETF"}'
```

Create a data preparation run:

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

Prepare data and inspect the run:

```bash
curl -X POST http://127.0.0.1:8000/api/runs/1/prepare-data
curl http://127.0.0.1:8000/api/runs/1
```

## Project Map

```text
.
├── src/foundlab/
│   ├── api/              # FastAPI app, schemas, asset routes, run routes
│   ├── core/             # Enums, models, provider protocols, normalization
│   ├── storage/          # SQLModel tables, database session, repositories
│   └── worker/           # Synchronous jobs and data preparation entry points
├── frontend/             # Vite + React dashboard
├── tests/                # Backend, API, storage, worker, and data tests
├── docs/superpowers/     # Design notes and implementation plans
└── skill/                # FoundLab agent workflow skill
```

## Architecture

FoundLab is a modular monolith. `foundlab.core` owns framework-independent contracts and
data processing. API, worker, and storage layers depend on core, while core stays free of
web and database concerns.

Current data flow:

1. API or agent creates an asset and a run.
2. Worker builds a `ProviderRequest` from the run config.
3. `AkShareProvider` fetches ETF, stock, or public fund daily data.
4. Normalization produces `NormalizedBar` records.
5. Storage saves raw provider rows, cleaned daily bars, and data warnings.
6. Run status becomes `succeeded`, `succeeded_with_warnings`, or `failed`.

## Development Notes

- Routine tests use fixtures or fake clients instead of live AkShare network access.
- Live AkShare calls are best treated as manual smoke tests or agent research runs.
- New data sources should implement `MarketDataProvider`.
- New strategies should emit neutral `OrderIntent` values before execution logic handles fills,
  non-trading days, cash constraints, and fees.
- Reports and dashboards should always show data source, fetch time, cleaning assumptions,
  execution rules, fee assumptions, and warning counts.

## Roadmap

- ETF daily fixed-investment baseline.
- CSV historical decision replay.
- Gross and net ledgers with a basic fee model.
- Return, annualized return, max drawdown, volatility, and trade-count metrics.
- Better warnings and execution rules for A-shares and public funds.
- Static report exports.
- Dashboard run history, report viewer, and multi-run comparison.

## Contributing

FoundLab is early, which means the useful edges are still very visible. Good contributions
include small data-provider improvements, focused tests, clearer docs, and narrow dashboard
views that make runs easier to inspect.

Before large changes, open an issue or write down the intended boundary: data contracts,
strategy execution, reporting, and dashboard UX are deliberately separated.

## License

FoundLab is released under the [MIT License](LICENSE).
