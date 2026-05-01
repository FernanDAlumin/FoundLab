import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.enums import AdjustmentMode, AssetType, RunStatus
from foundlab.storage.database import ensure_backtest_run_data_columns
from foundlab.storage.models import AssetRecord, BacktestRunRecord, utc_now
from foundlab.storage.repositories import (
    create_asset,
    create_run,
    get_assets_by_ids,
    get_run,
    list_assets,
    update_run_status,
)


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def make_shared_memory_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def test_utc_now_returns_naive_datetime() -> None:
    assert utc_now().tzinfo is None


def test_create_db_and_tables_registers_models_without_prior_import(tmp_path: Path) -> None:
    src_path = os.fspath((Path(__file__).parents[2] / "src").resolve())
    script = """
from sqlalchemy import inspect

from foundlab.storage import database

database.create_db_and_tables()
tables = set(inspect(database.engine).get_table_names())
assert {
    "assets",
    "backtest_runs",
    "raw_market_data",
    "clean_market_data_bars",
    "data_warnings",
}.issubset(tables), tables
"""
    env = {**os.environ, "PYTHONPATH": src_path}
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr


def test_ensure_backtest_run_data_columns_updates_existing_sqlite_table() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                create table backtest_runs (
                    id integer primary key,
                    name varchar not null,
                    strategy_name varchar not null,
                    asset_ids json not null,
                    status varchar not null,
                    warning_count integer not null,
                    error_message varchar,
                    created_at datetime not null,
                    updated_at datetime not null
                )
                """
            )
        )

    ensure_backtest_run_data_columns(engine)

    with engine.connect() as connection:
        columns = {
            row[1]: row[2]
            for row in connection.execute(text("pragma table_info(backtest_runs)"))
        }

    assert columns["start_date"].upper() == "DATE"
    assert columns["end_date"].upper() == "DATE"
    assert columns["adjustment"].upper() == "VARCHAR(3)"


def test_create_and_list_assets() -> None:
    with make_session() as session:
        asset = create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        assets = list_assets(session)

    assert asset.id is not None
    assert asset.created_at.tzinfo is None
    assert [item.asset_id for item in assets] == ["510300"]
    assert isinstance(assets[0].asset_type, AssetType)
    assert assets[0].asset_type == AssetType.ETF
    assert assets[0].created_at.tzinfo is None


def test_asset_type_persists_public_value() -> None:
    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        raw_asset_type = session.execute(text("select asset_type from assets")).one()[0]

    assert raw_asset_type == AssetType.ETF.value


def test_create_run_for_asset() -> None:
    with make_session() as session:
        asset = create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=[asset.asset_id],
            strategy_name="daily_dca",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            adjustment=AdjustmentMode.QFQ,
        )
        loaded = get_run(session, run.id)
        raw_asset_ids, raw_adjustment = session.execute(
            text("select asset_ids, adjustment from backtest_runs")
        ).one()

    assert loaded is not None
    assert loaded.name == "ETF baseline"
    assert loaded.asset_ids == ["510300"]
    assert loaded.start_date == date(2024, 1, 1)
    assert loaded.end_date == date(2024, 1, 31)
    assert loaded.adjustment == AdjustmentMode.QFQ
    assert isinstance(loaded.status, RunStatus)
    assert loaded.status == RunStatus.PENDING
    assert loaded.created_at.tzinfo is None
    assert loaded.updated_at.tzinfo is None
    assert raw_asset_ids == '["510300"]'
    assert raw_adjustment == AdjustmentMode.QFQ.value


def test_get_assets_by_ids_preserves_requested_order() -> None:
    with make_session() as session:
        create_asset(session, asset_id="000001", asset_type=AssetType.STOCK, name="平安银行")
        create_asset(session, asset_id="510300", asset_type=AssetType.ETF, name="沪深300ETF")

        assets = get_assets_by_ids(session, ["510300", "000001"])

    assert [asset.asset_id for asset in assets] == ["510300", "000001"]
    assert [asset.asset_type for asset in assets] == [AssetType.ETF, AssetType.STOCK]


def test_create_run_rejects_none_asset_ids() -> None:
    with make_session() as session:
        with pytest.raises(ValueError, match="asset_ids must be a list of strings"):
            create_run(
                session,
                name="ETF baseline",
                asset_ids=None,  # type: ignore[arg-type]
                strategy_name="daily_dca",
            )


@pytest.mark.parametrize("asset_ids", [[123], [None]])
def test_create_run_rejects_non_string_asset_ids(asset_ids: list[object]) -> None:
    with make_session() as session:
        with pytest.raises(ValueError, match="asset_ids must be a list of strings"):
            create_run(
                session,
                name="ETF baseline",
                asset_ids=asset_ids,  # type: ignore[arg-type]
                strategy_name="daily_dca",
            )


@pytest.mark.parametrize("asset_ids", [[123], [None]])
def test_backtest_run_record_rejects_non_string_asset_ids(
    asset_ids: list[object],
) -> None:
    with make_session() as session:
        with pytest.raises(ValueError, match="asset_ids must be a list of strings"):
            run = BacktestRunRecord(
                name="ETF baseline",
                asset_ids=asset_ids,
                strategy_name="daily_dca",
            )
            session.add(run)
            session.commit()


def test_backtest_run_record_rejects_invalid_asset_ids_assignment() -> None:
    run = BacktestRunRecord(
        name="ETF baseline",
        asset_ids=["510300"],
        strategy_name="daily_dca",
    )

    with pytest.raises(ValueError, match="asset_ids must be a list of strings"):
        run.asset_ids = [123]  # type: ignore[list-item]


def test_backtest_run_record_accepts_valid_asset_ids_assignment() -> None:
    run = BacktestRunRecord(
        name="ETF baseline",
        asset_ids=["510300"],
        strategy_name="daily_dca",
    )

    run.asset_ids = ["159915"]

    assert run.asset_ids == ["159915"]


def test_run_status_persists_public_value() -> None:
    with make_session() as session:
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
        )
        assert run.id is not None
        raw_status = session.execute(
            text("select status from backtest_runs where id = :run_id"),
            params={"run_id": run.id},
        ).one()[0]

    assert raw_status == RunStatus.PENDING.value


def test_update_run_status_persists_changes() -> None:
    engine = make_shared_memory_engine()

    with Session(engine) as session:
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
        )
        original_updated_at = run.updated_at

        update_run_status(
            session,
            run,
            status=RunStatus.FAILED,
            warning_count=2,
            error_message="bad data",
        )
        run_id = run.id
        assert run_id is not None

    with Session(engine) as session:
        loaded = get_run(session, run_id)
        raw_status, raw_error_message = session.execute(
            text("select status, error_message from backtest_runs where id = :run_id"),
            params={"run_id": run_id},
        ).one()

    assert loaded is not None
    assert loaded.status == RunStatus.FAILED
    assert loaded.warning_count == 2
    assert loaded.error_message == "bad data"
    assert loaded.updated_at != original_updated_at
    assert loaded.created_at.tzinfo is None
    assert loaded.updated_at.tzinfo is None
    assert raw_status == RunStatus.FAILED.value
    assert raw_error_message == "bad data"


def test_tables_are_importable_for_api_and_worker() -> None:
    assert AssetRecord.__tablename__ == "assets"
    assert BacktestRunRecord.__tablename__ == "backtest_runs"
