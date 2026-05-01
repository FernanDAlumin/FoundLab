from datetime import date

from pydantic import BaseModel, ConfigDict

from foundlab.core.enums import AdjustmentMode, AssetType, RunStatus


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
    start_date: date | None = None
    end_date: date | None = None
    adjustment: AdjustmentMode = AdjustmentMode.QFQ


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    asset_ids: list[str]
    strategy_name: str
    start_date: date | None
    end_date: date | None
    adjustment: AdjustmentMode
    status: RunStatus
    warning_count: int
    error_message: str | None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: int
    status: RunStatus
    warning_count: int
    bar_count: int
    error_message: str | None
