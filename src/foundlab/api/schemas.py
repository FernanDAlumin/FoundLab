from pydantic import BaseModel, ConfigDict

from foundlab.core.enums import AssetType, RunStatus


class AssetCreate(BaseModel):
    asset_id: str
    asset_type: AssetType
    name: str


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: str
    asset_type: AssetType
    name: str


class RunCreate(BaseModel):
    name: str
    asset_ids: list[str]
    strategy_name: str


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    asset_ids: list[str]
    strategy_name: str
    status: RunStatus
    warning_count: int
    error_message: str | None
