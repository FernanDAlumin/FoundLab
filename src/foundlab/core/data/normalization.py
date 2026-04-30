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

    if request.asset_type == AssetType.PUBLIC_FUND:
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
    if value is None or pd.isna(value):
        raise ValueError("Required decimal value is missing or non-finite")

    decimal_value = Decimal(str(value))
    if not decimal_value.is_finite():
        raise ValueError("Required decimal value is missing or non-finite")
    return decimal_value


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    return _decimal(value)
