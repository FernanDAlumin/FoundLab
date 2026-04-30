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
                "净值日期": ["2023-12-29", "2024-01-01", "2024-01-03", "2024-01-04"],
                "单位净值": [1.1, 1.2, 1.3, 1.4],
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
    assert client.calls == [
        (
            "stock_zh_a_hist",
            {
                "symbol": "000001",
                "period": "daily",
                "start_date": "20240101",
                "end_date": "20240131",
                "adjust": "hfq",
            },
        )
    ]


def test_fetch_daily_accepts_plain_storage_string_asset_type() -> None:
    client = FakeAkShareClient()
    provider = AkShareProvider(client=client)
    request = ProviderRequest(
        asset_id="510300",
        asset_type="etf",  # type: ignore[arg-type]
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


def test_fetch_public_fund_filters_nav_rows_by_date() -> None:
    client = FakeAkShareClient()
    provider = AkShareProvider(client=client)
    request = ProviderRequest(
        asset_id="710001",
        asset_type=AssetType.PUBLIC_FUND,
        start=date(2024, 1, 1),
        end=date(2024, 1, 3),
        adjustment=AdjustmentMode.NONE,
    )

    frame = provider.fetch_daily(request)

    assert frame["单位净值"].tolist() == [1.2, 1.3]
    assert client.calls == [
        (
            "fund_open_fund_info_em",
            {"symbol": "710001", "indicator": "单位净值走势"},
        )
    ]
