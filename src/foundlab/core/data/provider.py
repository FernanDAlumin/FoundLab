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
