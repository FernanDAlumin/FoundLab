from datetime import date

import pandas as pd
from sqlmodel import Session, SQLModel, create_engine, select

from foundlab.core.data.provider import ProviderRequest
from foundlab.core.enums import AdjustmentMode, AssetType, RunStatus
from foundlab.storage.models import BacktestRunRecord
from foundlab.storage.repositories import (
    create_asset,
    create_run,
    get_run,
    list_clean_market_data_bars,
    list_data_warnings,
    list_raw_market_data,
)
from foundlab.worker.jobs import run_data_preparation_job, run_foundation_job


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


class FakeProvider:
    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
        self.requests.append(request)
        return pd.DataFrame({"日期": ["2024-01-02"], "收盘": [3.5]})


class FailsOnAssetProvider:
    def __init__(self, failing_asset_id: str) -> None:
        self.failing_asset_id = failing_asset_id

    def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
        if request.asset_id == self.failing_asset_id:
            raise RuntimeError(f"fetch failed for {request.asset_id}")
        return pd.DataFrame({"日期": ["2024-01-02"], "收盘": [3.5]})


def test_foundation_job_marks_run_succeeded() -> None:
    with make_session() as session:
        run = create_run(
            session,
            name="Foundation smoke",
            asset_ids=["510300"],
            strategy_name="daily_dca",
        )
        assert run.id is not None
        result = run_foundation_job(session, run.id)
        loaded = get_run(session, run.id)

    assert result.run_id == run.id
    assert result.status == RunStatus.SUCCEEDED
    assert result.warning_count == 0
    assert result.error_message is None
    assert loaded is not None
    assert loaded.status == RunStatus.SUCCEEDED
    assert loaded.warning_count == 0


def test_data_preparation_job_fetches_and_cleans_run_assets() -> None:
    provider = FakeProvider()

    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            adjustment=AdjustmentMode.QFQ,
        )
        assert run.id is not None

        result = run_data_preparation_job(session, run.id, provider=provider)
        loaded = get_run(session, run.id)
        raw_records = list_raw_market_data(session, run.id)
        bar_records = list_clean_market_data_bars(session, run.id)
        warning_records = list_data_warnings(session, run.id)

    assert [request.asset_id for request in provider.requests] == ["510300"]
    assert result.status == RunStatus.SUCCEEDED
    assert result.bar_count == 1
    assert result.warning_count == 0
    assert loaded is not None
    assert loaded.status == RunStatus.SUCCEEDED
    assert len(raw_records) == 1
    assert raw_records[0].row_count == 1
    assert raw_records[0].rows == [{"日期": "2024-01-02", "收盘": 3.5}]
    assert len(bar_records) == 1
    assert bar_records[0].asset_id == "510300"
    assert bar_records[0].close == "3.5"
    assert warning_records == []


def test_data_preparation_job_marks_warning_status_for_empty_data() -> None:
    class EmptyProvider:
        def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
            return pd.DataFrame()

    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            adjustment=AdjustmentMode.QFQ,
        )
        assert run.id is not None

        result = run_data_preparation_job(session, run.id, provider=EmptyProvider())
        loaded = get_run(session, run.id)
        raw_records = list_raw_market_data(session, run.id)
        warning_records = list_data_warnings(session, run.id)

    assert result.status == RunStatus.SUCCEEDED_WITH_WARNINGS
    assert result.bar_count == 0
    assert result.warning_count == 1
    assert loaded is not None
    assert loaded.status == RunStatus.SUCCEEDED_WITH_WARNINGS
    assert loaded.warning_count == 1
    assert len(raw_records) == 1
    assert raw_records[0].row_count == 0
    assert raw_records[0].rows == []
    assert len(warning_records) == 1
    assert warning_records[0].code == "empty_provider_response"


def test_data_preparation_job_replaces_cached_rows_on_rerun() -> None:
    provider = FakeProvider()

    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            adjustment=AdjustmentMode.QFQ,
        )
        assert run.id is not None

        run_data_preparation_job(session, run.id, provider=provider)
        run_data_preparation_job(session, run.id, provider=provider)
        raw_records = list_raw_market_data(session, run.id)
        bar_records = list_clean_market_data_bars(session, run.id)

    assert len(raw_records) == 1
    assert len(bar_records) == 1


def test_data_preparation_job_failed_rerun_preserves_previous_cache() -> None:
    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        create_asset(
            session,
            asset_id="159915",
            asset_type=AssetType.ETF,
            name="创业板ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300", "159915"],
            strategy_name="daily_dca",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            adjustment=AdjustmentMode.QFQ,
        )
        assert run.id is not None

        first_result = run_data_preparation_job(session, run.id, provider=FakeProvider())
        failed_result = run_data_preparation_job(
            session,
            run.id,
            provider=FailsOnAssetProvider(failing_asset_id="159915"),
        )
        raw_records = list_raw_market_data(session, run.id)
        bar_records = list_clean_market_data_bars(session, run.id)

    assert first_result.status == RunStatus.SUCCEEDED
    assert failed_result.status == RunStatus.FAILED
    assert failed_result.error_message == "fetch failed for 159915"
    assert [record.asset_id for record in raw_records] == ["159915", "510300"]
    assert [record.asset_id for record in bar_records] == ["159915", "510300"]


def test_data_preparation_job_failed_run_reports_accumulated_warnings() -> None:
    class EmptyThenFailProvider:
        def fetch_daily(self, request: ProviderRequest) -> pd.DataFrame:
            if request.asset_id == "159915":
                raise RuntimeError("fetch failed for 159915")
            return pd.DataFrame()

    with make_session() as session:
        create_asset(
            session,
            asset_id="510300",
            asset_type=AssetType.ETF,
            name="沪深300ETF",
        )
        create_asset(
            session,
            asset_id="159915",
            asset_type=AssetType.ETF,
            name="创业板ETF",
        )
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300", "159915"],
            strategy_name="daily_dca",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            adjustment=AdjustmentMode.QFQ,
        )
        assert run.id is not None

        result = run_data_preparation_job(session, run.id, provider=EmptyThenFailProvider())
        loaded = get_run(session, run.id)
        raw_records = list_raw_market_data(session, run.id)
        warning_records = list_data_warnings(session, run.id)

    assert result.status == RunStatus.FAILED
    assert result.warning_count == 1
    assert loaded is not None
    assert loaded.warning_count == 1
    assert raw_records == []
    assert warning_records == []


def test_data_preparation_job_fails_when_run_dates_are_missing() -> None:
    with make_session() as session:
        run = create_run(
            session,
            name="ETF baseline",
            asset_ids=["510300"],
            strategy_name="daily_dca",
        )
        assert run.id is not None

        result = run_data_preparation_job(session, run.id, provider=FakeProvider())
        loaded = get_run(session, run.id)

    assert result.status == RunStatus.FAILED
    assert result.error_message == "Run must define start_date and end_date before fetching data"
    assert loaded is not None
    assert loaded.status == RunStatus.FAILED


def test_foundation_job_marks_missing_run_failed() -> None:
    with make_session() as session:
        result = run_foundation_job(session, 404)
        persisted_run_count = len(session.exec(select(BacktestRunRecord)).all())

    assert result.status == RunStatus.FAILED
    assert result.error_message == "Run 404 not found"
    assert persisted_run_count == 0
