from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from foundlab.api.schemas import RunCreate, RunRead
from foundlab.storage.database import get_session
from foundlab.storage.repositories import create_run, get_run

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
