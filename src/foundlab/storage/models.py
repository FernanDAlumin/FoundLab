from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, Enum
from sqlmodel import Field, SQLModel

from foundlab.core.enums import AssetType, RunStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


def enum_value_column(enum_cls: type[StrEnum]) -> Enum:
    return Enum(
        enum_cls,
        values_callable=lambda members: [member.value for member in members],
        native_enum=False,
    )


class AssetRecord(SQLModel, table=True):
    __tablename__ = "assets"

    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(index=True, unique=True)
    asset_type: AssetType = Field(
        sa_column=Column(enum_value_column(AssetType), index=True, nullable=False),
    )
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class BacktestRunRecord(SQLModel, table=True):
    __tablename__ = "backtest_runs"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    strategy_name: str
    asset_ids: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    status: RunStatus = Field(
        default=RunStatus.PENDING,
        sa_column=Column(enum_value_column(RunStatus), index=True, nullable=False),
    )
    warning_count: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
