from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from decimal import Decimal, DecimalException
from typing import cast

import pandas as pd

from foundlab.core.data.normalization import normalize_daily_frame
from foundlab.core.data.provider import MarketDataProvider, ProviderRequest
from foundlab.core.enums import AssetType, ProviderName
from foundlab.core.models import DataWarning, NormalizedBar

JsonScalar = str | int | float | bool | None
RawDataRow = dict[str, JsonScalar]


@dataclass(frozen=True)
class DailyDataResult:
    request: ProviderRequest
    raw_row_count: int
    raw_rows: tuple[RawDataRow, ...]
    bars: tuple[NormalizedBar, ...]
    warnings: tuple[DataWarning, ...]
    provider: ProviderName = ProviderName.AKSHARE
    interface: str = ""
    retrieved_at: datetime | None = None

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def fetch_and_clean_daily_data(
    *,
    provider: MarketDataProvider,
    request: ProviderRequest,
    provider_name: ProviderName = ProviderName.AKSHARE,
    interface: str | None = None,
    retrieved_at: datetime | None = None,
) -> DailyDataResult:
    fetched_at = retrieved_at or datetime.now(UTC)
    source_interface = interface or _default_interface_for(request.asset_type)
    frame = provider.fetch_daily(request)
    raw_rows = _frame_to_raw_rows(frame)

    if frame.empty:
        warning = DataWarning(
            code="empty_provider_response",
            message="Provider returned no daily rows",
            asset_id=request.asset_id,
        )
        return DailyDataResult(
            request=request,
            raw_row_count=0,
            raw_rows=(),
            bars=(),
            warnings=(warning,),
            provider=provider_name,
            interface=source_interface,
            retrieved_at=fetched_at,
        )

    bars: list[NormalizedBar] = []
    warnings: list[DataWarning] = []
    for _, row in frame.iterrows():
        row_frame = pd.DataFrame([row.to_dict()])
        try:
            normalized = normalize_daily_frame(
                frame=row_frame,
                request=request,
                provider=provider_name,
                interface=source_interface,
                retrieved_at=fetched_at,
            )
            if not normalized:
                continue
            bar = normalized[0]
            _validate_effective_price(bar)
        except (DecimalException, KeyError, TypeError, ValueError) as exc:
            warnings.append(
                DataWarning(
                    code="invalid_daily_row",
                    message=str(exc),
                    asset_id=request.asset_id,
                    date=_extract_row_date(row, request.asset_type),
                )
            )
            continue

        bars.append(bar)

    sorted_bars = tuple(sorted(bars, key=lambda bar: bar.date))
    warning_tuple = tuple(warnings)
    if warning_tuple:
        sorted_bars = tuple(
            replace(bar, meta=replace(bar.meta, warnings=warning_tuple))
            for bar in sorted_bars
        )

    return DailyDataResult(
        request=request,
        raw_row_count=len(frame.index),
        raw_rows=raw_rows,
        bars=sorted_bars,
        warnings=warning_tuple,
        provider=provider_name,
        interface=source_interface,
        retrieved_at=fetched_at,
    )


def _default_interface_for(asset_type: AssetType) -> str:
    normalized_asset_type = AssetType(asset_type)
    if normalized_asset_type == AssetType.ETF:
        return "fund_etf_hist_em"
    if normalized_asset_type == AssetType.STOCK:
        return "stock_zh_a_hist"
    if normalized_asset_type == AssetType.PUBLIC_FUND:
        return "fund_open_fund_info_em"
    raise ValueError(f"Unsupported asset type: {asset_type}")


def _extract_row_date(row: pd.Series, asset_type: AssetType) -> date | None:
    date_column = "净值日期" if AssetType(asset_type) == AssetType.PUBLIC_FUND else "日期"
    try:
        value = row.get(date_column)
        if value is None or pd.isna(value):
            return None
        return pd.Timestamp(value).date()
    except (TypeError, ValueError):
        return None


def _validate_effective_price(bar: NormalizedBar) -> None:
    if bar.effective_price is None or bar.effective_price <= Decimal("0"):
        raise ValueError("Effective price must be positive")


def _frame_to_raw_rows(frame: pd.DataFrame) -> tuple[RawDataRow, ...]:
    if frame.empty:
        return ()

    records_json = frame.to_json(
        orient="records",
        date_format="iso",
        force_ascii=False,
    )
    records = cast(list[RawDataRow], json.loads(records_json))
    return tuple(records)
