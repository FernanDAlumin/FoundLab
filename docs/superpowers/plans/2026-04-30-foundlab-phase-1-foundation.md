# FoundLab Phase 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working foundation for FoundLab: Python package scaffold, core contracts, AkShare provider boundary, SQLite metadata model, minimal API, minimal worker, and a dashboard shell.

**Architecture:** Use a modular monolith. The `foundlab.core` package owns provider-neutral contracts and data normalization; `foundlab.api`, `foundlab.storage`, and `foundlab.worker` depend on core but core does not import them. The frontend is a Vite React app that talks to the FastAPI API and stays thin in Phase 1.

**Tech Stack:** Python 3.11+, uv, FastAPI, SQLModel, SQLite, pandas, AkShare, pytest, React, Vite, TypeScript, Vitest.

---

## Scope Boundary

This plan implements Phase 1 from the approved design spec:

- Project scaffold and dependency configuration.
- Core data contracts.
- AkShare provider interface and boundary with fixture-driven tests.
- Minimal normalization for ETF, stock, and public fund daily data.
- SQLite-backed metadata for assets and backtest runs.
- Minimal FastAPI app for assets and runs.
- Minimal synchronous worker skeleton.
- Minimal dashboard shell.

This plan does not implement real strategy execution, CSV decision replay, metrics, report generation, or rich dashboard comparison views. Those belong in separate phase plans after this foundation is merged.

## File Structure

Create or modify these files:

- `pyproject.toml`: Python package metadata, dependencies, pytest, ruff, and mypy settings.
- `README.md`: local development commands and Phase 1 scope.
- `src/foundlab/__init__.py`: package version.
- `src/foundlab/py.typed`: typing marker.
- `src/foundlab/core/enums.py`: shared enums for assets, providers, statuses, and policies.
- `src/foundlab/core/models.py`: provider-neutral dataclasses used by core, API, worker, and tests.
- `src/foundlab/core/data/provider.py`: provider protocol and request object.
- `src/foundlab/core/data/akshare_provider.py`: injectable AkShare wrapper.
- `src/foundlab/core/data/normalization.py`: convert AkShare-like frames into `NormalizedBar` records.
- `src/foundlab/storage/database.py`: engine/session helpers.
- `src/foundlab/storage/models.py`: SQLModel tables.
- `src/foundlab/storage/repositories.py`: small persistence functions for API and worker.
- `src/foundlab/api/schemas.py`: Pydantic request/response schemas.
- `src/foundlab/api/main.py`: FastAPI app factory and health route.
- `src/foundlab/api/routes/assets.py`: asset endpoints.
- `src/foundlab/api/routes/runs.py`: run endpoints.
- `src/foundlab/worker/jobs.py`: synchronous Phase 1 job runner.
- `tests/test_package_import.py`: package smoke test.
- `tests/core/test_contracts.py`: core model tests.
- `tests/core/test_akshare_provider.py`: provider boundary tests with a fake client.
- `tests/core/test_normalization.py`: normalization fixture tests.
- `tests/storage/test_repositories.py`: SQLite repository tests.
- `tests/api/test_api.py`: API contract tests.
- `tests/worker/test_jobs.py`: worker status transition tests.
- `frontend/package.json`: frontend dependencies and scripts.
- `frontend/index.html`: Vite entry HTML.
- `frontend/tsconfig.json`: TypeScript config.
- `frontend/vite.config.ts`: Vite and Vitest config.
- `frontend/src/main.tsx`: React entry.
- `frontend/src/App.tsx`: dashboard shell.
- `frontend/src/App.css`: dashboard shell styling.
- `frontend/src/App.test.tsx`: dashboard shell test.
- `frontend/src/test/setup.ts`: Vitest setup.

## Task 1: Python Package Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/foundlab/__init__.py`
- Create: `src/foundlab/py.typed`
- Create: `tests/test_package_import.py`

- [ ] **Step 1: Write the failing package import test**

Create `tests/test_package_import.py`:

```python
def test_package_exposes_version() -> None:
    import foundlab

    assert foundlab.__version__ == "0.1.0"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_package_import.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab'`.

- [ ] **Step 3: Create package configuration and package marker files**

Create `pyproject.toml`:

```toml
[project]
name = "foundlab"
version = "0.1.0"
description = "Dashboard-first backtesting platform for investment decision review."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "akshare>=1.17",
    "fastapi>=0.115",
    "pandas>=2.2",
    "pydantic-settings>=2.6",
    "python-multipart>=0.0.12",
    "sqlmodel>=0.0.22",
    "uvicorn[standard]>=0.30",
]

[project.optional-dependencies]
dev = [
    "httpx>=0.27",
    "mypy>=1.13",
    "pytest>=8.3",
    "ruff>=0.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/foundlab"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_return_any = true
disallow_untyped_defs = true
```

Create `src/foundlab/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/foundlab/py.typed` as an empty file.

- [ ] **Step 4: Run the package import test**

Run:

```bash
uv run pytest tests/test_package_import.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add pyproject.toml src/foundlab/__init__.py src/foundlab/py.typed tests/test_package_import.py
git commit -m "chore: scaffold python package"
```

## Task 2: Core Domain Contracts

**Files:**
- Create: `src/foundlab/core/enums.py`
- Create: `src/foundlab/core/models.py`
- Test: `tests/core/test_contracts.py`

- [ ] **Step 1: Write failing tests for core contracts**

Create `tests/core/test_contracts.py`:

```python
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from foundlab.core.enums import (
    AdjustmentMode,
    AssetType,
    NonTradingDayPolicy,
    OrderSide,
    ProviderName,
    RunStatus,
)
from foundlab.core.models import DataWarning, NormalizedBar, OrderIntent, ProviderDatasetMeta


def test_normalized_bar_uses_adjusted_close_before_close() -> None:
    meta = ProviderDatasetMeta(
        provider=ProviderName.AKSHARE,
        interface="stock_zh_a_hist",
        retrieved_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
        asset_id="000001",
        asset_type=AssetType.STOCK,
        adjustment=AdjustmentMode.QFQ,
    )
    bar = NormalizedBar(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        date=date(2024, 1, 2),
        open=Decimal("9.80"),
        high=Decimal("10.30"),
        low=Decimal("9.70"),
        close=Decimal("10.00"),
        adjusted_close=Decimal("9.95"),
        volume=Decimal("1000"),
        tradable=True,
        meta=meta,
    )

    assert bar.effective_price == Decimal("9.95")


def test_normalized_bar_uses_nav_for_public_fund() -> None:
    meta = ProviderDatasetMeta(
        provider=ProviderName.AKSHARE,
        interface="fund_open_fund_info_em",
        retrieved_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        adjustment=AdjustmentMode.NONE,
    )
    bar = NormalizedBar(
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        date=date(2024, 1, 2),
        nav=Decimal("1.2345"),
        tradable=True,
        meta=meta,
    )

    assert bar.effective_price == Decimal("1.2345")


def test_normalized_bar_requires_a_price() -> None:
    meta = ProviderDatasetMeta(
        provider=ProviderName.AKSHARE,
        interface="fund_open_fund_info_em",
        retrieved_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        adjustment=AdjustmentMode.NONE,
    )

    with pytest.raises(ValueError, match="at least one price"):
        NormalizedBar(
            asset_id="710001",
            asset_type=AssetType.PUBLIC_FUND,
            date=date(2024, 1, 2),
            tradable=True,
            meta=meta,
        )


def test_order_intent_accepts_amount_or_quantity() -> None:
    intent = OrderIntent(
        intended_date=date(2024, 1, 2),
        asset_id="510300",
        asset_type=AssetType.ETF,
        side=OrderSide.BUY,
        amount=Decimal("100.00"),
        source="daily_dca",
        note="baseline",
        tags=("baseline", "dca"),
    )

    assert intent.amount == Decimal("100.00")
    assert intent.quantity is None


def test_order_intent_rejects_missing_amount_and_quantity() -> None:
    with pytest.raises(ValueError, match="amount or quantity"):
        OrderIntent(
            intended_date=date(2024, 1, 2),
            asset_id="510300",
            asset_type=AssetType.ETF,
            side=OrderSide.BUY,
            source="csv_replay",
        )


def test_enums_have_expected_storage_values() -> None:
    assert AssetType.ETF.value == "etf"
    assert AssetType.STOCK.value == "stock"
    assert AssetType.PUBLIC_FUND.value == "public_fund"
    assert ProviderName.AKSHARE.value == "akshare"
    assert AdjustmentMode.QFQ.value == "qfq"
    assert NonTradingDayPolicy.NEXT.value == "next"
    assert RunStatus.PENDING.value == "pending"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/core/test_contracts.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab.core'`.

- [ ] **Step 3: Implement core enums**

Create `src/foundlab/core/enums.py`:

```python
from enum import Enum


class AssetType(str, Enum):
    ETF = "etf"
    STOCK = "stock"
    PUBLIC_FUND = "public_fund"


class ProviderName(str, Enum):
    AKSHARE = "akshare"
    TUSHARE = "tushare"


class AdjustmentMode(str, Enum):
    NONE = ""
    QFQ = "qfq"
    HFQ = "hfq"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class NonTradingDayPolicy(str, Enum):
    FAIL = "fail"
    SKIP = "skip"
    NEXT = "next"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
```

- [ ] **Step 4: Implement core dataclasses**

Create `src/foundlab/core/models.py`:

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from foundlab.core.enums import AdjustmentMode, AssetType, OrderSide, ProviderName


@dataclass(frozen=True)
class DataWarning:
    code: str
    message: str
    asset_id: str | None = None
    date: date | None = None


@dataclass(frozen=True)
class ProviderDatasetMeta:
    provider: ProviderName
    interface: str
    retrieved_at: datetime
    asset_id: str
    asset_type: AssetType
    adjustment: AdjustmentMode
    warnings: tuple[DataWarning, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class NormalizedBar:
    asset_id: str
    asset_type: AssetType
    date: date
    tradable: bool
    meta: ProviderDatasetMeta
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal | None = None
    adjusted_close: Decimal | None = None
    nav: Decimal | None = None
    accumulated_nav: Decimal | None = None
    volume: Decimal | None = None

    def __post_init__(self) -> None:
        if self.effective_price is None:
            raise ValueError("NormalizedBar requires at least one price field")

    @property
    def effective_price(self) -> Decimal | None:
        return self.adjusted_close or self.close or self.nav or self.accumulated_nav


@dataclass(frozen=True)
class OrderIntent:
    intended_date: date
    asset_id: str
    asset_type: AssetType
    side: OrderSide
    source: str
    amount: Decimal | None = None
    quantity: Decimal | None = None
    intended_price: Decimal | None = None
    note: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.amount is None and self.quantity is None:
            raise ValueError("OrderIntent requires amount or quantity")
        if self.amount is not None and self.quantity is not None:
            raise ValueError("OrderIntent accepts amount or quantity, not both")
```

- [ ] **Step 5: Run the core contract tests**

Run:

```bash
uv run pytest tests/core/test_contracts.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/foundlab/core/enums.py src/foundlab/core/models.py tests/core/test_contracts.py
git commit -m "feat: add core domain contracts"
```

## Task 3: AkShare Provider Boundary

**Files:**
- Create: `src/foundlab/core/data/provider.py`
- Create: `src/foundlab/core/data/akshare_provider.py`
- Test: `tests/core/test_akshare_provider.py`

- [ ] **Step 1: Write failing provider boundary tests**

Create `tests/core/test_akshare_provider.py`:

```python
from datetime import date

import pandas as pd

from foundlab.core.data.akshare_provider import AkShareProvider
from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AdjustmentMode, AssetType


class FakeAkShareClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def fund_etf_hist_em(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame:
        self.calls.append(
            (
                "fund_etf_hist_em",
                {
                    "symbol": symbol,
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "adjust": adjust,
                },
            )
        )
        return pd.DataFrame({"日期": ["2024-01-02"], "收盘": [3.5]})

    def stock_zh_a_hist(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame:
        self.calls.append(
            (
                "stock_zh_a_hist",
                {
                    "symbol": symbol,
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "adjust": adjust,
                },
            )
        )
        return pd.DataFrame({"日期": ["2024-01-02"], "收盘": [10.5]})

    def fund_open_fund_info_em(self, *, symbol: str, indicator: str) -> pd.DataFrame:
        self.calls.append(
            (
                "fund_open_fund_info_em",
                {"symbol": symbol, "indicator": indicator},
            )
        )
        return pd.DataFrame(
            {
                "净值日期": ["2023-12-29", "2024-01-02", "2024-01-03"],
                "单位净值": [1.1, 1.2, 1.3],
            }
        )


def test_fetch_etf_daily_uses_fund_etf_hist_em() -> None:
    client = FakeAkShareClient()
    provider = AkShareProvider(client=client)
    request = ProviderRequest(
        asset_id="510300",
        asset_type=AssetType.ETF,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    frame = provider.fetch_daily(request)

    assert frame["收盘"].tolist() == [3.5]
    assert client.calls == [
        (
            "fund_etf_hist_em",
            {
                "symbol": "510300",
                "period": "daily",
                "start_date": "20240101",
                "end_date": "20240131",
                "adjust": "qfq",
            },
        )
    ]


def test_fetch_stock_daily_uses_stock_zh_a_hist() -> None:
    client = FakeAkShareClient()
    provider = AkShareProvider(client=client)
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.HFQ,
    )

    frame = provider.fetch_daily(request)

    assert frame["收盘"].tolist() == [10.5]
    assert client.calls[0][0] == "stock_zh_a_hist"
    assert client.calls[0][1]["adjust"] == "hfq"


def test_fetch_public_fund_filters_nav_rows_by_date() -> None:
    client = FakeAkShareClient()
    provider = AkShareProvider(client=client)
    request = ProviderRequest(
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        start=date(2024, 1, 1),
        end=date(2024, 1, 2),
        adjustment=AdjustmentMode.NONE,
    )

    frame = provider.fetch_daily(request)

    assert frame["单位净值"].tolist() == [1.2]
    assert client.calls == [
        (
            "fund_open_fund_info_em",
            {"symbol": "710001", "indicator": "单位净值走势"},
        )
    ]
```

- [ ] **Step 2: Run the provider tests to verify they fail**

Run:

```bash
uv run pytest tests/core/test_akshare_provider.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab.core.data'`.

- [ ] **Step 3: Implement provider request and protocol**

Create `src/foundlab/core/data/provider.py`:

```python
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import pandas as pd

from foundlab.core.enums import AdjustmentMode, AssetType


@dataclass(frozen=True)
class ProviderRequest:
    asset_id: str
    asset_type: AssetType
    start: date
    end: date
    adjustment: AdjustmentMode

    @property
    def start_yyyymmdd(self) -> str:
        return self.start.strftime("%Y%m%d")

    @property
    def end_yyyymmdd(self) -> str:
        return self.end.strftime("%Y%m%d")


class MarketDataProvider(Protocol):
    def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
        """Return a raw provider frame for the requested daily series."""
```

- [ ] **Step 4: Implement the injectable AkShare provider wrapper**

Create `src/foundlab/core/data/akshare_provider.py`:

```python
from datetime import date
from typing import Any

import pandas as pd

from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AssetType


class AkShareProvider:
    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            import akshare as ak

            client = ak
        self._client = client

    def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
        if request.asset_type is AssetType.ETF:
            return self._client.fund_etf_hist_em(
                symbol=request.asset_id,
                period="daily",
                start_date=request.start_yyyymmdd,
                end_date=request.end_yyyymmdd,
                adjust=request.adjustment.value,
            )

        if request.asset_type is AssetType.STOCK:
            return self._client.stock_zh_a_hist(
                symbol=request.asset_id,
                period="daily",
                start_date=request.start_yyyymmdd,
                end_date=request.end_yyyymmdd,
                adjust=request.adjustment.value,
            )

        if request.asset_type is AssetType.PUBLIC_FUND:
            frame = self._client.fund_open_fund_info_em(
                symbol=request.asset_id,
                indicator="单位净值走势",
            )
            return _filter_fund_nav_frame(frame, request.start, request.end)

        raise ValueError(f"Unsupported asset type: {request.asset_type}")


def _filter_fund_nav_frame(frame: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    if frame.empty:
        return frame

    filtered = frame.copy()
    filtered["净值日期"] = pd.to_datetime(filtered["净值日期"]).dt.date
    filtered = filtered[(filtered["净值日期"] >= start) & (filtered["净值日期"] <= end)]
    return filtered.reset_index(drop=True)
```

- [ ] **Step 5: Run the provider tests**

Run:

```bash
uv run pytest tests/core/test_akshare_provider.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/foundlab/core/data/provider.py src/foundlab/core/data/akshare_provider.py tests/core/test_akshare_provider.py
git commit -m "feat: add akshare provider boundary"
```

## Task 4: Normalize Daily Market Data

**Files:**
- Create: `src/foundlab/core/data/normalization.py`
- Test: `tests/core/test_normalization.py`

- [ ] **Step 1: Write failing normalization tests**

Create `tests/core/test_normalization.py`:

```python
from datetime import date, datetime, timezone
from decimal import Decimal

import pandas as pd

from foundlab.core.data.normalization import normalize_daily_frame
from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AdjustmentMode, AssetType, ProviderName


def test_normalize_stock_like_ohlcv_frame() -> None:
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )
    frame = pd.DataFrame(
        {
            "日期": ["2024-01-02"],
            "开盘": [9.8],
            "最高": [10.3],
            "最低": [9.7],
            "收盘": [10.0],
            "成交量": [1000],
        }
    )

    bars = normalize_daily_frame(
        frame=frame,
        request=request,
        provider=ProviderName.AKSHARE,
        interface="stock_zh_a_hist",
        retrieved_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
    )

    assert len(bars) == 1
    assert bars[0].asset_id == "000001"
    assert bars[0].date == date(2024, 1, 2)
    assert bars[0].close == Decimal("10.0")
    assert bars[0].adjusted_close == Decimal("10.0")
    assert bars[0].volume == Decimal("1000")


def test_normalize_public_fund_nav_frame() -> None:
    request = ProviderRequest(
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.NONE,
    )
    frame = pd.DataFrame({"净值日期": ["2024-01-02"], "单位净值": [1.2345]})

    bars = normalize_daily_frame(
        frame=frame,
        request=request,
        provider=ProviderName.AKSHARE,
        interface="fund_open_fund_info_em",
        retrieved_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
    )

    assert len(bars) == 1
    assert bars[0].date == date(2024, 1, 2)
    assert bars[0].nav == Decimal("1.2345")
    assert bars[0].effective_price == Decimal("1.2345")


def test_empty_frame_returns_empty_list() -> None:
    request = ProviderRequest(
        asset_id="510300",
        asset_type=AssetType.ETF,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    assert (
        normalize_daily_frame(
            frame=pd.DataFrame(),
            request=request,
            provider=ProviderName.AKSHARE,
            interface="fund_etf_hist_em",
            retrieved_at=datetime(2026, 4, 30, tzinfo=timezone.utc),
        )
        == []
    )
```

- [ ] **Step 2: Run the normalization tests to verify they fail**

Run:

```bash
uv run pytest tests/core/test_normalization.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab.core.data.normalization'`.

- [ ] **Step 3: Implement normalization**

Create `src/foundlab/core/data/normalization.py`:

```python
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AssetType, ProviderName
from foundlab.core.models import NormalizedBar, ProviderDatasetMeta


def normalize_daily_frame(
    *,
    frame: pd.DataFrame,
    request: ProviderRequest,
    provider: ProviderName,
    interface: str,
    retrieved_at: datetime,
) -> list[NormalizedBar]:
    if frame.empty:
        return []

    meta = ProviderDatasetMeta(
        provider=provider,
        interface=interface,
        retrieved_at=retrieved_at,
        asset_id=request.asset_id,
        asset_type=request.asset_type,
        adjustment=request.adjustment,
    )

    if request.asset_type is AssetType.PUBLIC_FUND:
        return [_normalize_fund_row(row, request, meta) for _, row in frame.iterrows()]

    return [_normalize_ohlcv_row(row, request, meta) for _, row in frame.iterrows()]


def _normalize_ohlcv_row(
    row: pd.Series,
    request: ProviderRequest,
    meta: ProviderDatasetMeta,
) -> NormalizedBar:
    close = _decimal(row["收盘"])
    return NormalizedBar(
        asset_id=request.asset_id,
        asset_type=request.asset_type,
        date=pd.to_datetime(row["日期"]).date(),
        open=_decimal_or_none(row.get("开盘")),
        high=_decimal_or_none(row.get("最高")),
        low=_decimal_or_none(row.get("最低")),
        close=close,
        adjusted_close=close,
        volume=_decimal_or_none(row.get("成交量")),
        tradable=True,
        meta=meta,
    )


def _normalize_fund_row(
    row: pd.Series,
    request: ProviderRequest,
    meta: ProviderDatasetMeta,
) -> NormalizedBar:
    return NormalizedBar(
        asset_id=request.asset_id,
        asset_type=request.asset_type,
        date=pd.to_datetime(row["净值日期"]).date(),
        nav=_decimal(row["单位净值"]),
        tradable=True,
        meta=meta,
    )


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    return _decimal(value)
```

- [ ] **Step 4: Run the normalization tests**

Run:

```bash
uv run pytest tests/core/test_normalization.py -q
```

Expected: PASS.

- [ ] **Step 5: Run all core tests**

Run:

```bash
uv run pytest tests/core -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/foundlab/core/data/normalization.py tests/core/test_normalization.py
git commit -m "feat: normalize daily market data"
```

## Task 5: SQLite Metadata Storage

**Files:**
- Create: `src/foundlab/storage/database.py`
- Create: `src/foundlab/storage/models.py`
- Create: `src/foundlab/storage/repositories.py`
- Test: `tests/storage/test_repositories.py`

- [ ] **Step 1: Write failing repository tests**

Create `tests/storage/test_repositories.py`:

```python
from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.enums import AssetType, RunStatus
from foundlab.storage.models import AssetRecord, BacktestRunRecord
from foundlab.storage.repositories import create_asset, create_run, get_run, list_assets


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_create_and_list_assets() -> None:
    with make_session() as session:
        asset = create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        assets = list_assets(session)

    assert asset.id is not None
    assert [item.asset_id for item in assets] == ["510300"]
    assert assets[0].asset_type == AssetType.ETF


def test_create_run_for_asset() -> None:
    with make_session() as session:
        asset = create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=[asset.asset_id],
            strategy_name="daily_dca",
        )
        loaded = get_run(session, run.id)

    assert loaded is not None
    assert loaded.name == "ETF baseline"
    assert loaded.asset_ids == ["510300"]
    assert loaded.status == RunStatus.PENDING


def test_tables_are_importable_for_api_and_worker() -> None:
    assert AssetRecord.__tablename__ == "assets"
    assert BacktestRunRecord.__tablename__ == "backtest_runs"
```

- [ ] **Step 2: Run the storage tests to verify they fail**

Run:

```bash
uv run pytest tests/storage/test_repositories.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab.storage'`.

- [ ] **Step 3: Implement database helpers**

Create `src/foundlab/storage/database.py`:

```python
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./foundlab.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

- [ ] **Step 4: Implement SQLModel records**

Create `src/foundlab/storage/models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from foundlab.core.enums import AssetType, RunStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AssetRecord(SQLModel, table=True):
    __tablename__ = "assets"

    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, unique=True)
    asset_type: AssetType = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class BacktestRunRecord(SQLModel, table=True):
    __tablename__ = "backtest_runs"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    strategy_name: str
    asset_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: RunStatus = Field(default=RunStatus.PENDING, index=True)
    warning_count: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
```

- [ ] **Step 5: Implement repositories**

Create `src/foundlab/storage/repositories.py`:

```python
from sqlmodel import Session, select

from foundlab.core.enums import AssetType, RunStatus
from foundlab.storage.models import AssetRecord, BacktestRunRecord, utc_now


def create_asset(
    session: Session,
    *,
    asset_id: str,
    asset_type: AssetType,
    name: str,
) -> AssetRecord:
    asset = AssetRecord(asset_id=asset_id, asset_type=asset_type, name=name)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def list_assets(session: Session) -> list[AssetRecord]:
    statement = select(AssetRecord).order_by(AssetRecord.asset_id)
    return list(session.exec(statement))


def create_run(
    session: Session,
    *,
    name: str,
    asset_ids: list[str],
    strategy_name: str,
) -> BacktestRunRecord:
    run = BacktestRunRecord(
        name=name,
        asset_ids=asset_ids,
        strategy_name=strategy_name,
        status=RunStatus.PENDING,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: int | None) -> BacktestRunRecord | None:
    if run_id is None:
        return None
    return session.get(BacktestRunRecord, run_id)


def update_run_status(
    session: Session,
    run: BacktestRunRecord,
    *,
    status: RunStatus,
    warning_count: int | None = None,
    error_message: str | None = None,
) -> BacktestRunRecord:
    run.status = status
    run.updated_at = utc_now()
    if warning_count is not None:
        run.warning_count = warning_count
    run.error_message = error_message
    session.add(run)
    session.commit()
    session.refresh(run)
    return run
```

- [ ] **Step 6: Run the storage tests**

Run:

```bash
uv run pytest tests/storage/test_repositories.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add src/foundlab/storage tests/storage/test_repositories.py
git commit -m "feat: add sqlite metadata storage"
```

## Task 6: Minimal FastAPI App

**Files:**
- Create: `src/foundlab/api/schemas.py`
- Create: `src/foundlab/api/main.py`
- Create: `src/foundlab/api/routes/assets.py`
- Create: `src/foundlab/api/routes/runs.py`
- Test: `tests/api/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/api/test_api.py`:

```python
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from foundlab.api.main import create_app
from foundlab.storage.database import get_session


def make_test_client() -> TestClient:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    app = create_app()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def test_health() -> None:
    client = make_test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "foundlab-api"}


def test_create_and_list_assets() -> None:
    client = make_test_client()

    created = client.post(
        "/api/assets",
        json={"asset_id": "510300", "asset_type": "etf", "name": "沪深300ETF"},
    )
    listed = client.get("/api/assets")

    assert created.status_code == 201
    assert created.json()["asset_id"] == "510300"
    assert listed.status_code == 200
    assert listed.json() == [
        {"id": 1, "asset_id": "510300", "asset_type": "etf", "name": "沪深300ETF"}
    ]


def test_create_and_get_run() -> None:
    client = make_test_client()

    response = client.post(
        "/api/runs",
        json={
            "name": "ETF baseline",
            "asset_ids": ["510300"],
            "strategy_name": "daily_dca",
        },
    )
    run_id = response.json()["id"]
    loaded = client.get(f"/api/runs/{run_id}")

    assert response.status_code == 201
    assert loaded.status_code == 200
    assert loaded.json()["status"] == "pending"
    assert loaded.json()["asset_ids"] == ["510300"]
```

- [ ] **Step 2: Run the API tests to verify they fail**

Run:

```bash
uv run pytest tests/api/test_api.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab.api'`.

- [ ] **Step 3: Implement API schemas**

Create `src/foundlab/api/schemas.py`:

```python
from pydantic import BaseModel, ConfigDict

from foundlab.core.enums import AssetType, RunStatus


class AssetCreate(BaseModel):
    asset_id: str
    asset_type: AssetType
    name: str


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: str
    asset_type: AssetType
    name: str


class RunCreate(BaseModel):
    name: str
    asset_ids: list[str]
    strategy_name: str


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    asset_ids: list[str]
    strategy_name: str
    status: RunStatus
    warning_count: int
    error_message: str | None
```

- [ ] **Step 4: Implement asset routes**

Create `src/foundlab/api/routes/assets.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from foundlab.api.schemas import AssetCreate, AssetRead
from foundlab.storage.database import get_session
from foundlab.storage.repositories import create_asset, list_assets

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset_endpoint(
    payload: AssetCreate,
    session: Annotated[Session, Depends(get_session)],
) -> AssetRead:
    return AssetRead.model_validate(
        create_asset(
            session,
            asset_id=payload.asset_id,
            asset_type=payload.asset_type,
            name=payload.name,
        )
    )


@router.get("", response_model=list[AssetRead])
def list_assets_endpoint(session: Annotated[Session, Depends(get_session)]) -> list[AssetRead]:
    return [AssetRead.model_validate(asset) for asset in list_assets(session)]
```

- [ ] **Step 5: Implement run routes**

Create `src/foundlab/api/routes/runs.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from foundlab.api.schemas import RunCreate, RunRead
from foundlab.storage.database import get_session
from foundlab.storage.repositories import create_run, get_run

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run_endpoint(
    payload: RunCreate,
    session: Annotated[Session, Depends(get_session)],
) -> RunRead:
    return RunRead.model_validate(
        create_run(
            session,
            name=payload.name,
            asset_ids=payload.asset_ids,
            strategy_name=payload.strategy_name,
        )
    )


@router.get("/{run_id}", response_model=RunRead)
def get_run_endpoint(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> RunRead:
    run = get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunRead.model_validate(run)
```

- [ ] **Step 6: Implement app factory**

Create `src/foundlab/api/main.py`:

```python
from fastapi import FastAPI

from foundlab.api.routes import assets, runs
from foundlab.storage.database import create_db_and_tables


def create_app() -> FastAPI:
    app = FastAPI(title="FoundLab API", version="0.1.0")

    @app.on_event("startup")
    def on_startup() -> None:
        create_db_and_tables()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "foundlab-api"}

    app.include_router(assets.router)
    app.include_router(runs.router)
    return app


app = create_app()
```

- [ ] **Step 7: Run the API tests**

Run:

```bash
uv run pytest tests/api/test_api.py -q
```

Expected: PASS.

- [ ] **Step 8: Start the API locally and check health**

Run:

```bash
uv run uvicorn foundlab.api.main:app --reload
```

In another terminal, run:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"foundlab-api"}
```

Stop uvicorn with `Ctrl-C`.

- [ ] **Step 9: Commit**

Run:

```bash
git add src/foundlab/api tests/api/test_api.py
git commit -m "feat: add minimal api"
```

## Task 7: Minimal Worker Job Runner

**Files:**
- Create: `src/foundlab/worker/jobs.py`
- Test: `tests/worker/test_jobs.py`

- [ ] **Step 1: Write failing worker tests**

Create `tests/worker/test_jobs.py`:

```python
from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.enums import RunStatus
from foundlab.storage.repositories import create_run, get_run
from foundlab.worker.jobs import run_foundation_job


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_foundation_job_marks_run_succeeded() -> None:
    with make_session() as session:
        run = create_run(
            session,
            name="Foundation smoke",
            asset_ids=["510300"],
            strategy_name="daily_dca",
        )
        result = run_foundation_job(session, run.id)
        loaded = get_run(session, run.id)

    assert result.status == RunStatus.SUCCEEDED
    assert loaded is not None
    assert loaded.status == RunStatus.SUCCEEDED
    assert loaded.warning_count == 0


def test_foundation_job_marks_missing_run_failed() -> None:
    with make_session() as session:
        result = run_foundation_job(session, 404)

    assert result.status == RunStatus.FAILED
    assert result.error_message == "Run 404 not found"
```

- [ ] **Step 2: Run the worker tests to verify they fail**

Run:

```bash
uv run pytest tests/worker/test_jobs.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'foundlab.worker'`.

- [ ] **Step 3: Implement the worker skeleton**

Create `src/foundlab/worker/jobs.py`:

```python
from dataclasses import dataclass

from sqlmodel import Session

from foundlab.core.enums import RunStatus
from foundlab.storage.repositories import get_run, update_run_status


@dataclass(frozen=True)
class JobResult:
    run_id: int
    status: RunStatus
    warning_count: int
    error_message: str | None = None


def run_foundation_job(session: Session, run_id: int) -> JobResult:
    run = get_run(session, run_id)
    if run is None:
        return JobResult(
            run_id=run_id,
            status=RunStatus.FAILED,
            warning_count=0,
            error_message=f"Run {run_id} not found",
        )

    update_run_status(session, run, status=RunStatus.RUNNING)
    updated = update_run_status(session, run, status=RunStatus.SUCCEEDED, warning_count=0)
    return JobResult(
        run_id=updated.id or run_id,
        status=updated.status,
        warning_count=updated.warning_count,
        error_message=updated.error_message,
    )
```

- [ ] **Step 4: Run worker tests**

Run:

```bash
uv run pytest tests/worker/test_jobs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/foundlab/worker/jobs.py tests/worker/test_jobs.py
git commit -m "feat: add minimal worker job runner"
```

## Task 8: Dashboard Shell

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/App.css`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Write frontend package configuration**

Create `frontend/package.json`:

```json
{
  "name": "foundlab-dashboard",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest --run",
    "lint": "tsc -b --noEmit"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "lucide-react": "^0.468.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "vite": "^7.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "jsdom": "^25.0.0",
    "typescript": "^5.7.0",
    "vitest": "^3.0.0"
  }
}
```

- [ ] **Step 2: Write the failing dashboard shell test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the FoundLab dashboard shell", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "FoundLab" })).toBeInTheDocument();
    expect(screen.getByText("Assets")).toBeInTheDocument();
    expect(screen.getByText("Backtest Runs")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
  });
});
```

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 3: Run the frontend test to verify it fails**

Run:

```bash
npm --prefix frontend install
npm --prefix frontend test
```

Expected: FAIL because `frontend/src/App.tsx` does not exist.

- [ ] **Step 4: Create Vite config and TypeScript config**

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts"
  }
});
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "types": ["vitest/globals"]
  },
  "include": ["src", "vite.config.ts"],
  "references": []
}
```

- [ ] **Step 5: Create Vite entry files**

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FoundLab</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./App.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 6: Implement the dashboard shell**

Create `frontend/src/App.tsx`:

```tsx
import { Activity, BarChart3, Database, FileText } from "lucide-react";

const sections = [
  {
    title: "Assets",
    description: "ETF, A-share stock, and public fund universe.",
    icon: Database
  },
  {
    title: "Backtest Runs",
    description: "Create runs and track execution status.",
    icon: Activity
  },
  {
    title: "Reports",
    description: "Open static HTML, Markdown, chart, and CSV artifacts.",
    icon: FileText
  }
];

export default function App() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>FoundLab</h1>
          <p>Investment decision backtesting dashboard</p>
        </div>
        <button className="icon-button" type="button" aria-label="Open reports">
          <BarChart3 size={20} />
        </button>
      </header>

      <section className="summary-grid" aria-label="Dashboard sections">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <article className="summary-card" key={section.title}>
              <Icon size={22} aria-hidden="true" />
              <h2>{section.title}</h2>
              <p>{section.description}</p>
            </article>
          );
        })}
      </section>
    </main>
  );
}
```

Create `frontend/src/App.css`:

```css
:root {
  color: #17202a;
  background: #f4f6f8;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
  margin: 0;
}

button {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  padding: 32px;
  box-sizing: border-box;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: 0 auto 28px;
  max-width: 1120px;
}

.topbar h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.15;
}

.topbar p {
  margin: 8px 0 0;
  color: #52606d;
}

.icon-button {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #c9d2dc;
  border-radius: 8px;
  color: #17202a;
  background: #ffffff;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 0 auto;
  max-width: 1120px;
}

.summary-card {
  min-height: 142px;
  padding: 18px;
  border: 1px solid #d8dee6;
  border-radius: 8px;
  background: #ffffff;
  box-sizing: border-box;
}

.summary-card h2 {
  margin: 14px 0 8px;
  font-size: 18px;
}

.summary-card p {
  margin: 0;
  color: #52606d;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .app-shell {
    padding: 20px;
  }

  .topbar {
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Run frontend tests and build**

Run:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Expected: both commands PASS.

- [ ] **Step 8: Commit**

Run:

```bash
git add frontend
git commit -m "feat: add dashboard shell"
```

## Task 9: Documentation And Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with local development commands**

Replace `README.md` content with:

````markdown
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
````

- [ ] **Step 2: Run backend verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
```

Expected: both commands PASS.

- [ ] **Step 3: Run frontend verification**

Run:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Expected: both commands PASS.

- [ ] **Step 4: Check Git status**

Run:

```bash
git status --short --ignored
```

Expected: only ignored generated directories such as `.superpowers/`, `.venv/`, `frontend/node_modules/`, and `frontend/dist/` may appear as ignored. All source and test changes should be staged or committed.

- [ ] **Step 5: Commit README update**

Run:

```bash
git add README.md
git commit -m "docs: document phase 1 development workflow"
```

## Final Verification

Run these commands after all tasks are complete:

```bash
uv run pytest -q
uv run ruff check .
npm --prefix frontend test
npm --prefix frontend run build
git status --short --ignored
```

Expected:

- Python tests PASS.
- Ruff PASS.
- Frontend tests PASS.
- Frontend build PASS.
- Git status has no unstaged source changes.

## Implementation Notes

- Keep `foundlab.core` independent from FastAPI, SQLModel, and React.
- Do not add live AkShare calls to the normal test suite.
- Use fake clients and fixed pandas frames for provider tests.
- Use SQLite for Phase 1 metadata.
- Keep worker execution synchronous in Phase 1 so the run lifecycle is easy to test.
