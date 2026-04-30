from sqlmodel import Session, SQLModel, create_engine

from foundlab.core.enums import RunStatus
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
        result = run_foundation_job(session, run.id)
        loaded = get_run(session, run.id)

    assert result.status == RunStatus.SUCCEEDED
    assert loaded is not None
    assert loaded.status == RunStatus.SUCCEEDED
    assert loaded.warning_count == 0


def test_foundation_job_marks_missing_run_failed() -> None:
    with make_session() as session:
        result = run_foundation_job(session, 404)

    assert result.status == RunStatus.FAILED
    assert result.error_message == "Run 404 not found"
