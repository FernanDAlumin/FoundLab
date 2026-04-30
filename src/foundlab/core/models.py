from __future__ import annotations

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
        for price in (self.adjusted_close, self.close, self.nav, self.accumulated_nav):
            if price is not None:
                return price
        return None


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
