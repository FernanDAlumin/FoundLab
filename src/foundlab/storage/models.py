from datetime import UTC, datetime
from datetime import date as Date
from enum import StrEnum

from sqlalchemy import JSON, Column, Enum
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel

from foundlab.core.enums import AdjustmentMode, AssetType, ProviderName, RunStatus

JsonScalar = str | int | float | bool | None


def utc_now() -> datetime:
    # SQLite stores datetimes without timezone metadata; keep record values naive UTC.
    return datetime.now(UTC).replace(tzinfo=None)


def enum_value_column(enum_cls: type[StrEnum]) -> Enum:
    return Enum(
        enum_cls,
        values_callable=lambda members: [member.value for member in members],
        native_enum=False,
    )


def validate_asset_ids_value(value: object) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(asset_id, str) for asset_id in value
    ):
        raise ValueError("asset_ids must be a list of strings")
    return value


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
    start_date: Date | None = None
    end_date: Date | None = None
    adjustment: AdjustmentMode = Field(
        default=AdjustmentMode.QFQ,
        sa_column=Column(enum_value_column(AdjustmentMode), nullable=False),
    )
    status: RunStatus = Field(
        default=RunStatus.PENDING,
        sa_column=Column(enum_value_column(RunStatus), index=True, nullable=False),
    )
    warning_count: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @validates("asset_ids")
    def validate_asset_ids(self, _key: str, value: object) -> list[str]:
        return validate_asset_ids_value(value)


class RawMarketDataRecord(SQLModel, table=True):
    __tablename__ = "raw_market_data"

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    asset_id: str = Field(index=True)
    asset_type: AssetType = Field(
        sa_column=Column(enum_value_column(AssetType), index=True, nullable=False),
    )
    provider: ProviderName = Field(
        sa_column=Column(enum_value_column(ProviderName), index=True, nullable=False),
    )
    interface: str
    adjustment: AdjustmentMode = Field(
        sa_column=Column(enum_value_column(AdjustmentMode), nullable=False),
    )
    start_date: Date
    end_date: Date
    retrieved_at: datetime
    row_count: int
    rows: list[dict[str, JsonScalar]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(default_factory=utc_now)


class CleanMarketDataBarRecord(SQLModel, table=True):
    __tablename__ = "clean_market_data_bars"

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    asset_id: str = Field(index=True)
    asset_type: AssetType = Field(
        sa_column=Column(enum_value_column(AssetType), index=True, nullable=False),
    )
    provider: ProviderName = Field(
        sa_column=Column(enum_value_column(ProviderName), index=True, nullable=False),
    )
    interface: str
    adjustment: AdjustmentMode = Field(
        sa_column=Column(enum_value_column(AdjustmentMode), nullable=False),
    )
    date: Date = Field(index=True)
    open: str | None = None
    high: str | None = None
    low: str | None = None
    close: str | None = None
    adjusted_close: str | None = None
    nav: str | None = None
    accumulated_nav: str | None = None
    volume: str | None = None
    tradable: bool
    retrieved_at: datetime
    created_at: datetime = Field(default_factory=utc_now)


class DataWarningRecord(SQLModel, table=True):
    __tablename__ = "data_warnings"

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    asset_id: str | None = Field(default=None, index=True)
    date: Date | None = Field(default=None, index=True)
    code: str = Field(index=True)
    message: str
    created_at: datetime = Field(default_factory=utc_now)
