from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from foundlab.api.schemas import JobRead, RunCreate, RunRead
from foundlab.storage.database import get_session
from foundlab.storage.repositories import create_run, get_run
from foundlab.worker.jobs import run_data_preparation_job

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def post_run(
    run: RunCreate,
    session: Annotated[Session, Depends(get_session)],
) -> RunRead:
    created = create_run(
        session,
        name=run.name,
        asset_ids=run.asset_ids,
        strategy_name=run.strategy_name,
        start_date=run.start_date,
        end_date=run.end_date,
        adjustment=run.adjustment,
    )
    return RunRead.model_validate(created)


@router.get("/{run_id}", response_model=RunRead)
def get_run_by_id(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> RunRead:
    run = get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunRead.model_validate(run)


@router.post("/{run_id}/prepare-data", response_model=JobRead)
def prepare_run_data(
    run_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> JobRead:
    return JobRead.model_validate(run_data_preparation_job(session, run_id))
