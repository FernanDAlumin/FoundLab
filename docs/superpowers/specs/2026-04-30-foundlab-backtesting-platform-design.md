# FoundLab Backtesting Platform Design

Date: 2026-04-30

## Purpose

FoundLab is a platform for backtesting previous investment decisions and comparing them with standard baseline strategies. The first product shape is a service-first dashboard platform, not a pure CLI or notebook workflow. The system should support Chinese market ETF, A-share stock, and public fund backtests, starting with AkShare as the default data source.

The first version focuses on daily-level research and reporting. It does not support live trading, order placement, portfolio synchronization with brokers, multi-user permissions, or intraday execution.

## Product Scope

The platform supports two strategy input families:

- Standard strategy templates, starting with daily fixed investment and later extending to weekly fixed investment and fixed-ratio rebalancing.
- Historical decision replay, starting with CSV import and leaving a clear adapter boundary for future broker-export importers.

Reports compare a user decision replay against one or more baseline strategies. Every run records the data source, data retrieval time, cleaning assumptions, execution rules, fee assumptions, warnings, generated metrics, and report artifacts.

## Architecture

FoundLab uses a modular monolith architecture with a dashboard-first user experience:

- Dashboard: create assets, configure strategies, upload decision logs, start backtests, view run status, open reports, and compare recent runs.
- API: persist configuration, validate inputs, enqueue jobs, expose run status, and serve report metadata.
- Worker: fetch data, clean data, execute backtests, calculate metrics, and generate report artifacts.
- Core library: define data contracts, data adapters, cleaning logic, strategy generation, decision replay, execution simulation, fee handling, metrics, and charts.
- Storage: persist metadata in a relational database and report/data artifacts in files.

The core library must remain independent from the web framework. API and worker code call the core library, but the core library does not import dashboard or API modules. This keeps the backtesting engine deterministic, testable, and reusable from a future CLI or notebook.

## Data Source Strategy

AkShare is the default first-version data provider. It does not require an API key for normal use, which makes it suitable for bootstrapping the project. The design must still treat AkShare as an external, unstable source because public interfaces can change, fields can drift, and requests can intermittently fail.

TuShare and other providers are out of scope for the first implementation, but the data layer should define a provider interface so they can be added later. A future TuShare provider should read credentials from configuration, such as `TUSHARE_TOKEN`, without changing the backtesting engine.

Every fetched dataset should record:

- Provider name.
- Provider interface or adapter name.
- Retrieval timestamp.
- Library version when available.
- Asset identifier and asset type.
- Adjustment or net-value mode.
- Data quality warnings.

## Data Model And Cleaning

The data layer has separate adapters for ETF, A-share stock, and public fund data. Each adapter converts raw provider output into a shared normalized contract called `NormalizedSeries`.

`NormalizedSeries` should include:

- Asset identifier and asset type.
- Date.
- Open, high, low, close, and adjusted close when available.
- Unit net value and accumulated net value when available.
- Volume or turnover fields when available.
- Tradable flag.
- Source provider and source interface.
- Adjustment mode or fund net-value mode.
- Data quality warnings.

ETF and stock backtests mainly use OHLCV and adjusted close data. Public fund backtests mainly use unit net value or accumulated net value, with execution rules that model subscription and redemption at daily net value rather than intraday exchange prices.

The system keeps both raw and cleaned data:

- Raw cache preserves provider responses for traceability.
- Clean cache stores normalized data used by the backtest engine.

Cleaning must not silently hide issues. Missing dates, suspensions, delayed fund net values, abnormal prices, adjustment inconsistencies, and empty provider responses should produce warnings. Execution configuration decides whether affected orders fail, skip, or move to the next valid date.

## Strategy And Decision Replay

Strategies do not directly mutate portfolio state. They produce `OrderIntent` records. Historical decision replay also converts imported rows into the same `OrderIntent` contract.

`OrderIntent` should include:

- Intended date.
- Asset identifier.
- Side: buy or sell.
- Amount or quantity.
- Optional intended price.
- Source: strategy template, CSV decision log, or future broker importer.
- Reason or note.
- Tags.

Standard strategy templates generate intents from configuration and calendar rules. The first baseline is daily fixed investment. Later templates can add weekly fixed investment and fixed-ratio rebalancing without changing execution or reporting contracts.

CSV decision replay is the first historical-decision importer. The CSV template should support at least date, asset code, asset type, side, amount or quantity, optional price, fee fields, note, and tags. Broker-specific importers are future adapters that should convert external exports into the same internal intent format.

## Execution And Fees

Execution is separate from strategy generation. The execution layer converts `OrderIntent` into fills by applying:

- Asset tradability.
- Trading calendar or fund net-value calendar.
- Price selection rule.
- Non-trading-day behavior: fail, skip, or move to next valid date.
- Cash and position constraints.
- Fee model.

Reports must show both gross and net results:

- Gross ledger: ignores fees to show strategy economics before transaction costs.
- Net ledger: applies configured fees to approximate realized results.

The fee model should be configurable. The first version should support commission rate, minimum commission, stamp duty where applicable, and simple fund subscription/redemption fees. More detailed broker-specific or holding-period-specific fee schedules can be added later.

The execution layer produces a portfolio timeline with daily cash, positions, market value, total equity, cumulative contribution, gross result, net result, and executed trade records.

## Metrics

Each run calculates comparable metrics for every strategy variant:

- Total return.
- Annualized return when the time range supports it.
- Maximum drawdown.
- Volatility.
- Cumulative contribution.
- Ending market value.
- Gross-versus-net fee impact.
- Trade count.
- Data warning count.

For historical decision replay, the report should compare the replay against the baseline strategy over the same assets and date range where possible. The report should highlight how much fees, missed dates, skipped trades, and execution assumptions affected the result.

## Reports And Artifacts

The dashboard is the main navigation surface, but every backtest run also produces durable static artifacts:

- HTML report.
- Markdown summary.
- PNG charts.
- CSV result tables.

The report should include:

- Strategy and replay configuration.
- Asset list and date range.
- Data source details.
- Cleaning and adjustment assumptions.
- Fee assumptions.
- Execution rules.
- Data quality warnings.
- Equity curve comparison.
- Drawdown curve.
- Cumulative contribution and market value curve.
- Trade timeline.
- Metrics table.
- Links or references to generated artifacts.

Static reports should be reviewable without rerunning the dashboard. Dashboard pages can embed or link to these artifacts.

## Dashboard Scope

The first dashboard version should stay narrow:

- Asset list and asset detail.
- Strategy configuration form.
- CSV decision-log upload.
- Backtest run creation.
- Run status view.
- Report list.
- Report detail or report viewer.
- Simple comparison of recent runs.

The first version should not include multi-user permissions, scheduled background updates, notification systems, complex interactive chart builders, broker account linking, or live trading features.

## Error Handling

Errors are grouped by layer:

- Data source errors: AkShare failures, network timeouts, empty responses, or unexpected field changes.
- Data quality errors: missing trading days, suspensions, delayed fund values, abnormal prices, or inconsistent adjustment modes.
- Execution errors: invalid CSV rows, missing prices, unavailable trading dates, insufficient cash, or invalid order quantities.
- Report errors: chart generation failure, missing metrics, or artifact write failure.

Each run should have a clear status: pending, running, succeeded, succeeded with warnings, or failed. Warnings should be visible in both the dashboard and generated reports. Fatal errors should include enough context to reproduce the failure without exposing raw stack traces as the primary user message.

## Testing Strategy

Testing should prioritize deterministic core behavior:

- Unit tests for strategy templates, order-intent generation, fee calculation, execution rules, portfolio timeline updates, and metrics.
- Fixture-based adapter tests using fixed AkShare-like response samples rather than live network calls.
- Report-generation tests that verify required assumptions, metrics, warnings, and artifact paths appear.
- API tests for creating assets, creating runs, checking status, and retrieving report metadata.
- Minimal dashboard flow tests for creating a run and opening its generated report.

Live AkShare integration tests can exist as optional smoke tests, but they should not be required for the normal test suite because public data interfaces may fail for reasons outside the project.

## Implementation Phasing

The architecture is dashboard-first, but implementation should be staged to control risk:

1. Foundation: project scaffold, core contracts, database schema, job model, minimal API, minimal dashboard shell, and AkShare provider boundary.
2. Backtest correctness: ETF path, daily fixed-investment baseline, CSV decision replay, gross/net ledgers, and metrics tests.
3. Asset coverage: A-share stock and public fund adapters, asset-specific cleaning warnings, and asset-specific fee/execution variants.
4. Dashboard and report depth: report viewer, comparison view, richer run history, and static artifact export polish.

This phasing keeps the long-term platform direction while validating the most important source of risk first: correctness of data normalization and backtest accounting.

## Open Decisions For Implementation Planning

The implementation plan should decide concrete technology choices for:

- Python package and dependency manager.
- Web framework.
- Frontend framework.
- Database.
- Background job runner.
- Charting library.
- Report rendering approach.
- Local development workflow.

Those choices should be made during planning, based on the repository state and the desired speed of first implementation.
