from dataclasses import dataclass

from sqlmodel import Session

from foundlab.core.enums import RunStatus
from foundlab.storage.repositories import get_run, update_run_status


@dataclass(frozen=True)
class JobResult:
    run_id: int
    status: RunStatus
    warning_count: int
    error_message: str | None = None


def run_foundation_job(session: Session, run_id: int) -> JobResult:
    run = get_run(session, run_id)
    if run is None:
        return JobResult(
            run_id=run_id,
            status=RunStatus.FAILED,
            warning_count=0,
            error_message=f"Run {run_id} not found",
        )

    update_run_status(session, run, status=RunStatus.RUNNING)
    updated = update_run_status(session, run, status=RunStatus.SUCCEEDED, warning_count=0)
    return JobResult(
        run_id=updated.id or run_id,
        status=updated.status,
        warning_count=updated.warning_count,
        error_message=updated.error_message,
    )
