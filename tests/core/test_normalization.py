from datetime import UTC, date, datetime
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
        retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
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
        retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
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
            retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
        )
        == []
    )
