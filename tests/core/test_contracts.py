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
    amount_intent = OrderIntent(
        intended_date=date(2024, 1, 2),
        asset_id="510300",
        asset_type=AssetType.ETF,
        side=OrderSide.BUY,
        amount=Decimal("100.00"),
        source="daily_dca",
        note="baseline",
        tags=("baseline", "dca"),
    )
    quantity_intent = OrderIntent(
        intended_date=date(2024, 1, 2),
        asset_id="510300",
        asset_type=AssetType.ETF,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        source="daily_dca",
    )

    assert amount_intent.amount == Decimal("100.00")
    assert amount_intent.quantity is None
    assert quantity_intent.amount is None
    assert quantity_intent.quantity == Decimal("10")


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
    assert ProviderName.TUSHARE.value == "tushare"
    assert AdjustmentMode.NONE.value == ""
    assert AdjustmentMode.QFQ.value == "qfq"
    assert AdjustmentMode.HFQ.value == "hfq"
    assert NonTradingDayPolicy.FAIL.value == "fail"
    assert NonTradingDayPolicy.SKIP.value == "skip"
    assert NonTradingDayPolicy.NEXT.value == "next"
    assert RunStatus.PENDING.value == "pending"
    assert RunStatus.RUNNING.value == "running"
    assert RunStatus.SUCCEEDED.value == "succeeded"
    assert RunStatus.SUCCEEDED_WITH_WARNINGS.value == "succeeded_with_warnings"
    assert RunStatus.FAILED.value == "failed"
