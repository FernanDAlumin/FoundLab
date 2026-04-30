from datetime import UTC, date, datetime
from decimal import Decimal

import pandas as pd
import pytest

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
        retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
    )

    assert len(bars) == 1
    assert bars[0].asset_id == "000001"
    assert bars[0].date == date(2024, 1, 2)
    assert bars[0].close == Decimal("10.0")
    assert bars[0].adjusted_close == Decimal("10.0")
    assert bars[0].volume == Decimal("1000")
    assert bars[0].meta.provider == ProviderName.AKSHARE
    assert bars[0].meta.interface == "stock_zh_a_hist"
    assert bars[0].meta.retrieved_at == datetime(2026, 4, 30, tzinfo=UTC)
    assert bars[0].meta.asset_id == "000001"
    assert bars[0].meta.asset_type == AssetType.STOCK
    assert bars[0].meta.adjustment == AdjustmentMode.QFQ


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
        retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
    )

    assert len(bars) == 1
    assert bars[0].date == date(2024, 1, 2)
    assert bars[0].nav == Decimal("1.2345")
    assert bars[0].effective_price == Decimal("1.2345")
    assert bars[0].meta.provider == ProviderName.AKSHARE
    assert bars[0].meta.interface == "fund_open_fund_info_em"
    assert bars[0].meta.retrieved_at == datetime(2026, 4, 30, tzinfo=UTC)
    assert bars[0].meta.asset_id == "710001"
    assert bars[0].meta.asset_type == AssetType.PUBLIC_FUND
    assert bars[0].meta.adjustment == AdjustmentMode.NONE


def test_required_stock_close_nan_raises_value_error() -> None:
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
            "收盘": [float("nan")],
        }
    )

    with pytest.raises(ValueError, match="Required decimal value is missing or non-finite"):
        normalize_daily_frame(
            frame=frame,
            request=request,
            provider=ProviderName.AKSHARE,
            interface="stock_zh_a_hist",
            retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
        )


def test_required_public_fund_nav_nan_raises_value_error() -> None:
    request = ProviderRequest(
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.NONE,
    )
    frame = pd.DataFrame({"净值日期": ["2024-01-02"], "单位净值": [float("nan")]})

    with pytest.raises(ValueError, match="Required decimal value is missing or non-finite"):
        normalize_daily_frame(
            frame=frame,
            request=request,
            provider=ProviderName.AKSHARE,
            interface="fund_open_fund_info_em",
            retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
        )


def test_optional_ohlcv_missing_values_become_none() -> None:
    request = ProviderRequest(
        asset_id="510300",
        asset_type=AssetType.ETF,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )
    frame = pd.DataFrame(
        {
            "日期": ["2024-01-02"],
            "开盘": [None],
            "最高": [3.5],
            "最低": [3.4],
            "收盘": [3.45],
            "成交量": [pd.NA],
        }
    )

    bars = normalize_daily_frame(
        frame=frame,
        request=request,
        provider=ProviderName.AKSHARE,
        interface="fund_etf_hist_em",
        retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
    )

    assert len(bars) == 1
    assert bars[0].open is None
    assert bars[0].volume is None
    assert bars[0].high == Decimal("3.5")
    assert bars[0].low == Decimal("3.4")
    assert bars[0].close == Decimal("3.45")


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
            retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
        )
        == []
    )
