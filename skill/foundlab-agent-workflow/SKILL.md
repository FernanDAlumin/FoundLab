---
name: foundlab-agent-workflow
description: Use when working in FoundLab through an agent to fetch market data, prepare normalized daily bars, run fixed-investment comparisons, or report backtest results using the existing Python infra.
---

# FoundLab Agent Workflow

## Overview

Use this skill to operate FoundLab as an agent-driven research tool. Prefer the
existing provider, worker, and storage layers before adding framework code.

## Workflow

1. Clarify only missing run inputs: asset code, asset type, date range,
   investment cadence, amount, and fee assumptions.
2. Inspect the current repo state with `git status --short` before editing or
   writing data. Do not include unrelated dirty files in commits.
3. Use existing infra for data preparation:
   - `foundlab.core.data.akshare_provider.AkShareProvider`
   - `foundlab.core.data.provider.ProviderRequest`
   - `foundlab.worker.jobs.run_data_preparation_job`
   - `foundlab.storage.repositories` query helpers
4. For public funds, request `AssetType.PUBLIC_FUND` with
   `AdjustmentMode.NONE` unless the user specifies otherwise.
5. If live AkShare access fails because of sandboxed network or proxy settings,
   rerun the same operation through the approved escalation flow. Prefer
   clearing proxy environment variables for live data commands:
   `env -u http_proxy -u https_proxy -u all_proxy no_proxy='*' NO_PROXY='*' ...`.
6. Store downloaded data through a normal FoundLab run instead of ad hoc files:
   create the asset if missing, create a run with the requested date range, run
   `run_data_preparation_job`, then read `clean_market_data_bars` and
   `data_warnings`.
7. Compute results from cleaned bars, not raw provider rows.
8. Verify by re-reading the database counts and date range before reporting.

## Fixed-Investment Conventions

When the user asks to compare daily, weekly, and monthly fixed investment with a
daily amount, use this default unless they state a different budget model:

- Daily: invest the daily amount on every valid cleaned bar date.
- Weekly: group cleaned bar dates by ISO week and invest that week's accumulated
  daily budget on the first valid bar date of the week.
- Monthly: group cleaned bar dates by month and invest that month's accumulated
  daily budget on the first valid bar date of the month.
- Mark positions to the last cleaned bar in the requested range.
- Default to no fees, no taxes, and same-day execution at public fund unit NAV.

Always state these assumptions in the final result. If the user asks for a true
weekly or monthly fixed amount instead of equal total budget, use their amount
and call out that totals differ across strategies.

## Reporting

Report a compact table with:

- strategy name
- trade count
- total contribution
- final value
- profit/loss
- simple return percentage
- average cost
- first and last trade dates when useful

Include verification evidence: run id, clean bar count, warning count, actual
data date range, and the command or query class used to confirm it. Keep
generated database rows out of git unless the user explicitly asks to version
sample data.
