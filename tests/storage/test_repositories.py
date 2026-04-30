from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.enums import AssetType, RunStatus
from foundlab.storage.models import AssetRecord, BacktestRunRecord
from foundlab.storage.repositories import (
    create_asset,
    create_run,
    get_run,
    list_assets,
    update_run_status,
)


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


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
    assert [item.asset_id for item in assets] == ["510300"]
    assert assets[0].asset_type == AssetType.ETF


def test_asset_type_persists_public_value() -> None:
    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        raw_asset_type = session.exec(text("select asset_type from assets")).one()[0]

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
        )
        loaded = get_run(session, run.id)
        raw_asset_ids = session.exec(text("select asset_ids from backtest_runs")).one()[0]

    assert loaded is not None
    assert loaded.name == "ETF baseline"
    assert loaded.asset_ids == ["510300"]
    assert loaded.status == RunStatus.PENDING
    assert raw_asset_ids == '["510300"]'


def test_run_status_persists_public_value() -> None:
    with make_session() as session:
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
        )
        raw_status = session.exec(
            text("select status from backtest_runs where id = :run_id"),
            params={"run_id": run.id},
        ).one()[0]

    assert raw_status == RunStatus.PENDING.value


def test_update_run_status_persists_changes() -> None:
    with make_session() as session:
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
        loaded = get_run(session, run.id)

    assert loaded is not None
    assert loaded.status == RunStatus.FAILED
    assert loaded.warning_count == 2
    assert loaded.error_message == "bad data"
    assert loaded.updated_at != original_updated_at


def test_tables_are_importable_for_api_and_worker() -> None:
    assert AssetRecord.__tablename__ == "assets"
    assert BacktestRunRecord.__tablename__ == "backtest_runs"
