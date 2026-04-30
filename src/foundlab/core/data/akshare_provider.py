from datetime import date
from typing import Protocol, cast

import pandas as pd

from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AssetType


class AkShareClient(Protocol):
    def fund_etf_hist_em(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame: ...

    def stock_zh_a_hist(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame: ...

    def fund_open_fund_info_em(self, *, symbol: str, indicator: str) -> pd.DataFrame: ...


class AkShareProvider:
    def __init__(self, client: AkShareClient | None = None) -> None:
        if client is None:
            import akshare as ak

            client = cast(AkShareClient, ak)
        self._client = client

    def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
        if request.asset_type == AssetType.ETF:
            return self._client.fund_etf_hist_em(
                symbol=request.asset_id,
                period="daily",
                start_date=request.start_yyyymmdd,
                end_date=request.end_yyyymmdd,
                adjust=request.adjustment.value,
            )

        if request.asset_type == AssetType.STOCK:
            return self._client.stock_zh_a_hist(
                symbol=request.asset_id,
                period="daily",
                start_date=request.start_yyyymmdd,
                end_date=request.end_yyyymmdd,
                adjust=request.adjustment.value,
            )

        if request.asset_type == AssetType.PUBLIC_FUND:
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
