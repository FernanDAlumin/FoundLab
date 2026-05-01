from datetime import UTC, date, datetime
from decimal import Decimal

import pandas as pd

from foundlab.core.data.pipeline import fetch_and_clean_daily_data
from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AdjustmentMode, AssetType, ProviderName


class FakeDailyProvider:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.requests: list[ProviderRequest] = []

    def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
        self.requests.append(request)
        return self.frame


def test_fetch_and_clean_daily_data_normalizes_provider_rows() -> None:
    provider = FakeDailyProvider(
        pd.DataFrame(
            {
                "日期": ["2024-01-03", "2024-01-02"],
                "开盘": [10.2, 9.8],
                "最高": [10.5, 10.3],
                "最低": [10.1, 9.7],
                "收盘": [10.4, 10.0],
                "成交量": [1200, 1000],
            }
        )
    )
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )
    retrieved_at = datetime(2026, 4, 30, tzinfo=UTC)

    result = fetch_and_clean_daily_data(
        provider=provider,
        request=request,
        provider_name=ProviderName.AKSHARE,
        retrieved_at=retrieved_at,
    )

    assert provider.requests == [request]
    assert result.raw_row_count == 2
    assert result.raw_rows == (
        {
            "日期": "2024-01-03",
            "开盘": 10.2,
            "最高": 10.5,
            "最低": 10.1,
            "收盘": 10.4,
            "成交量": 1200,
        },
        {
            "日期": "2024-01-02",
            "开盘": 9.8,
            "最高": 10.3,
            "最低": 9.7,
            "收盘": 10.0,
            "成交量": 1000,
        },
    )
    assert result.warning_count == 0
    assert [bar.date for bar in result.bars] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert result.bars[0].close == Decimal("10.0")
    assert result.bars[0].meta.interface == "stock_zh_a_hist"
    assert result.bars[0].meta.retrieved_at == retrieved_at


def test_fetch_and_clean_daily_data_drops_invalid_rows_with_warnings() -> None:
    provider = FakeDailyProvider(
        pd.DataFrame(
            {
                "日期": ["2024-01-02", "2024-01-03", "2024-01-04"],
                "收盘": [10.0, float("nan"), -1.0],
            }
        )
    )
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    result = fetch_and_clean_daily_data(provider=provider, request=request)

    assert [bar.date for bar in result.bars] == [date(2024, 1, 2)]
    assert result.warning_count == 2
    assert [warning.code for warning in result.warnings] == [
        "invalid_daily_row",
        "invalid_daily_row",
    ]
    assert [warning.date for warning in result.warnings] == [
        date(2024, 1, 3),
        date(2024, 1, 4),
    ]
    assert all(bar.meta.warnings == result.warnings for bar in result.bars)


def test_fetch_and_clean_daily_data_bad_numeric_strings_become_row_warnings() -> None:
    provider = FakeDailyProvider(
        pd.DataFrame(
            {
                "日期": ["2024-01-02", "2024-01-03"],
                "收盘": [10.0, "bad"],
            }
        )
    )
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    result = fetch_and_clean_daily_data(provider=provider, request=request)

    assert [bar.date for bar in result.bars] == [date(2024, 1, 2)]
    assert result.warning_count == 1
    assert result.warnings[0].code == "invalid_daily_row"
    assert result.warnings[0].date == date(2024, 1, 3)


def test_fetch_and_clean_daily_data_raw_rows_convert_missing_values_to_none() -> None:
    provider = FakeDailyProvider(
        pd.DataFrame(
            {
                "日期": ["2024-01-02"],
                "开盘": [pd.NA],
                "收盘": [10.0],
            }
        )
    )
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    result = fetch_and_clean_daily_data(provider=provider, request=request)

    assert result.raw_rows == (
        {"日期": "2024-01-02", "开盘": None, "收盘": 10},
    )


def test_fetch_and_clean_daily_data_raw_rows_are_json_safe() -> None:
    provider = FakeDailyProvider(
        pd.DataFrame(
            {
                "日期": [pd.Timestamp("2024-01-02")],
                "开盘": [Decimal("9.80")],
                "收盘": [10.0],
                "备注": [float("nan")],
            }
        )
    )
    request = ProviderRequest(
        asset_id="000001",
        asset_type=AssetType.STOCK,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    result = fetch_and_clean_daily_data(provider=provider, request=request)

    assert result.raw_rows == (
            {
                "日期": "2024-01-02T00:00:00.000",
                "开盘": "9.80",
                "收盘": 10.0,
                "备注": None,
            },
    )


def test_fetch_and_clean_daily_data_warns_on_empty_provider_response() -> None:
    provider = FakeDailyProvider(pd.DataFrame())
    request = ProviderRequest(
        asset_id="510300",
        asset_type=AssetType.ETF,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )

    result = fetch_and_clean_daily_data(provider=provider, request=request)

    assert result.bars == ()
    assert result.raw_rows == ()
    assert result.raw_row_count == 0
    assert result.warning_count == 1
    assert result.warnings[0].code == "empty_provider_response"
    assert result.warnings[0].asset_id == "510300"
