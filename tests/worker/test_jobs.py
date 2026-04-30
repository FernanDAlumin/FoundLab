from sqlmodel import Session, SQLModel, create_engine, select

from foundlab.core.enums import RunStatus
from foundlab.storage.models import BacktestRunRecord
from foundlab.storage.repositories import create_run, get_run
from foundlab.worker.jobs import run_foundation_job


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


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


def test_foundation_job_marks_missing_run_failed() -> None:
    with make_session() as session:
        result = run_foundation_job(session, 404)
        persisted_run_count = len(session.exec(select(BacktestRunRecord)).all())

    assert result.status == RunStatus.FAILED
    assert result.error_message == "Run 404 not found"
    assert persisted_run_count == 0
