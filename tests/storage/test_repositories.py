import pytest
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.enums import AssetType, RunStatus
from foundlab.storage.models import AssetRecord, BacktestRunRecord, utc_now
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


def make_shared_memory_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def test_utc_now_returns_naive_datetime() -> None:
    assert utc_now().tzinfo is None


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
    assert isinstance(loaded.status, RunStatus)
    assert loaded.status == RunStatus.PENDING
    assert loaded.created_at.tzinfo is None
    assert loaded.updated_at.tzinfo is None
    assert raw_asset_ids == '["510300"]'


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
                asset_ids=asset_ids,  # type: ignore[arg-type]
                strategy_name="daily_dca",
            )
            session.add(run)
            session.commit()


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

    with Session(engine) as session:
        loaded = get_run(session, run_id)
        raw_status, raw_error_message = session.exec(
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
