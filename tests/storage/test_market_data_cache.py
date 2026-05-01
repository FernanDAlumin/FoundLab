from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.data.pipeline import DailyDataResult
from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AdjustmentMode, AssetType, ProviderName
from foundlab.core.models import DataWarning, NormalizedBar, ProviderDatasetMeta
from foundlab.storage.repositories import (
    clear_market_data_for_run,
    list_clean_market_data_bars,
    list_data_warnings,
    list_raw_market_data,
    save_market_data_result,
)


def make_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def make_result() -> DailyDataResult:
    request = ProviderRequest(
        asset_id="510300",
        asset_type=AssetType.ETF,
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        adjustment=AdjustmentMode.QFQ,
    )
    warning = DataWarning(
        code="invalid_daily_row",
        message="bad price",
        asset_id="510300",
        date=date(2024, 1, 3),
    )
    meta = ProviderDatasetMeta(
        provider=ProviderName.AKSHARE,
        interface="fund_etf_hist_em",
        retrieved_at=datetime(2026, 4, 30, tzinfo=UTC),
        asset_id="510300",
        asset_type=AssetType.ETF,
        adjustment=AdjustmentMode.QFQ,
        warnings=(warning,),
    )
    bar = NormalizedBar(
        asset_id="510300",
        asset_type=AssetType.ETF,
        date=date(2024, 1, 2),
        open=Decimal("3.2"),
        high=Decimal("3.3"),
        low=Decimal("3.1"),
        close=Decimal("3.25"),
        adjusted_close=Decimal("3.25"),
        volume=Decimal("1000"),
        tradable=True,
        meta=meta,
    )
    return DailyDataResult(
        request=request,
        raw_row_count=2,
        raw_rows=(
            {"日期": "2024-01-02", "收盘": 3.25},
            {"日期": "2024-01-03", "收盘": -1},
        ),
        bars=(bar,),
        warnings=(warning,),
    )


def test_save_market_data_result_persists_raw_clean_and_warnings() -> None:
    engine = make_engine()
    with Session(engine) as session:
        save_market_data_result(session, run_id=42, result=make_result())

    with Session(engine) as session:
        raw_records = list_raw_market_data(session, 42)
        bar_records = list_clean_market_data_bars(session, 42)
        warning_records = list_data_warnings(session, 42)

    assert len(raw_records) == 1
    assert raw_records[0].run_id == 42
    assert raw_records[0].asset_id == "510300"
    assert raw_records[0].provider == ProviderName.AKSHARE
    assert raw_records[0].interface == "fund_etf_hist_em"
    assert raw_records[0].row_count == 2
    assert raw_records[0].rows == [
        {"日期": "2024-01-02", "收盘": 3.25},
        {"日期": "2024-01-03", "收盘": -1},
    ]

    assert len(bar_records) == 1
    assert bar_records[0].run_id == 42
    assert bar_records[0].date == date(2024, 1, 2)
    assert bar_records[0].close == "3.25"
    assert bar_records[0].adjusted_close == "3.25"
    assert bar_records[0].volume == "1000"

    assert len(warning_records) == 1
    assert warning_records[0].code == "invalid_daily_row"
    assert warning_records[0].message == "bad price"
    assert warning_records[0].date == date(2024, 1, 3)


def test_clear_market_data_for_run_removes_cached_rows() -> None:
    engine = make_engine()
    with Session(engine) as session:
        save_market_data_result(session, run_id=42, result=make_result())
        clear_market_data_for_run(session, 42)

    with Session(engine) as session:
        raw_records = list_raw_market_data(session, 42)
        bar_records = list_clean_market_data_bars(session, 42)
        warning_records = list_data_warnings(session, 42)

    assert raw_records == []
    assert bar_records == []
    assert warning_records == []
