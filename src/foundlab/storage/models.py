from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from foundlab.core.enums import AssetType, RunStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class AssetRecord(SQLModel, table=True):
    __tablename__ = "assets"

    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, unique=True)
    asset_type: AssetType = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class BacktestRunRecord(SQLModel, table=True):
    __tablename__ = "backtest_runs"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    strategy_name: str
    asset_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: RunStatus = Field(default=RunStatus.PENDING, index=True)
    warning_count: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
