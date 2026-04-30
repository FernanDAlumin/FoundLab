from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from foundlab.api.schemas import AssetCreate, AssetRead
from foundlab.storage.database import get_session
from foundlab.storage.repositories import create_asset, list_assets

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def post_asset(
    asset: AssetCreate,
    session: Annotated[Session, Depends(get_session)],
) -> AssetRead:
    created = create_asset(
        session,
        asset_id=asset.asset_id,
        asset_type=asset.asset_type,
        name=asset.name,
    )
    return AssetRead.model_validate(created)


@router.get("", response_model=list[AssetRead])
def get_assets(session: Annotated[Session, Depends(get_session)]) -> list[AssetRead]:
    return [AssetRead.model_validate(asset) for asset in list_assets(session)]
