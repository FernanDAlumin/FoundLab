# FoundLab

FoundLab is a dashboard-first backtesting platform for reviewing investment decisions against baseline strategies.

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
