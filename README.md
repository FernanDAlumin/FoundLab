# FoundLab

[中文 README](README.zh.md)

FoundLab is a dashboard-first backtesting platform for reviewing investment decisions against baseline strategies.

## Usage Modes

FoundLab currently supports two practical ways to work with the project.

### 1. Agent Skill Workflow

Use the project-local skill at `skill/foundlab-agent-workflow/` when you want an
agent to operate FoundLab directly: fetch AkShare data, prepare normalized daily
bars, run fixed-investment comparisons, and report verified results.

Example request:

```text
Use $foundlab-agent-workflow to download 019058 public fund data from 2026-01-01
to 2026-04-30 and compare daily, weekly, and monthly fixed investment with
12 CNY per valid NAV day.
```

The skill is designed for research runs that reuse the existing Python infra and
avoid adding framework code unless the requested workflow needs new product
behavior.

### 2. Backend And Frontend Apps

Use the backend and frontend development commands below when you want to run the
API and dashboard locally.

## Phase 1 Scope

The current implementation foundation includes:

- Python package scaffold.
- Provider-neutral core contracts.
- AkShare provider boundary.
- Daily ETF, stock, and public fund normalization fixtures.
- SQLite metadata storage for assets and backtest runs.
- Minimal FastAPI API.
- Minimal synchronous worker skeleton.
- Minimal React dashboard shell.

Strategy execution, CSV decision replay, metrics, and report generation are covered by separate implementation phases.

## Backend Development

Install and test:

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
```

Run the API:

```bash
uv run uvicorn foundlab.api.main:app --reload
```

Check health:

```bash
curl http://127.0.0.1:8000/health
```

## Frontend Development

Install and test:

```bash
npm --prefix frontend install
npm --prefix frontend test
npm --prefix frontend run build
```

Run the dashboard:

```bash
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`.
