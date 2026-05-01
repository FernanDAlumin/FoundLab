from datetime import UTC, date, datetime
from decimal import Decimal

from sqlmodel import Session, col, delete, select

from foundlab.core.data.pipeline import DailyDataResult
from foundlab.core.enums import AdjustmentMode, AssetType, RunStatus
from foundlab.storage.models import (
    AssetRecord,
    BacktestRunRecord,
    CleanMarketDataBarRecord,
    DataWarningRecord,
    RawMarketDataRecord,
    utc_now,
    validate_asset_ids_value,
)


def create_asset(
    session: Session,
    *,
    asset_id: str,
    asset_type: AssetType,
    name: str,
) -> AssetRecord:
    asset = AssetRecord(asset_id=asset_id, asset_type=asset_type, name=name)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def list_assets(session: Session) -> list[AssetRecord]:
    statement = select(AssetRecord).order_by(AssetRecord.asset_id)
    return list(session.exec(statement))


def get_assets_by_ids(session: Session, asset_ids: list[str]) -> list[AssetRecord]:
    if not asset_ids:
        return []

    statement = select(AssetRecord).where(col(AssetRecord.asset_id).in_(asset_ids))
    records_by_id = {asset.asset_id: asset for asset in session.exec(statement)}
    return [
        records_by_id[asset_id]
        for asset_id in asset_ids
        if asset_id in records_by_id
    ]


def create_run(
    session: Session,
    *,
    name: str,
    asset_ids: list[str],
    strategy_name: str,
    start_date: date | None = None,
    end_date: date | None = None,
    adjustment: AdjustmentMode = AdjustmentMode.QFQ,
) -> BacktestRunRecord:
    validate_asset_ids_value(asset_ids)

    run = BacktestRunRecord(
        name=name,
        asset_ids=asset_ids,
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        adjustment=adjustment,
        status=RunStatus.PENDING,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: int | None) -> BacktestRunRecord | None:
    if run_id is None:
        return None
    return session.get(BacktestRunRecord, run_id)


def update_run_status(
    session: Session,
    run: BacktestRunRecord,
    *,
    status: RunStatus,
    warning_count: int | None = None,
    error_message: str | None = None,
) -> BacktestRunRecord:
    run.status = status
    run.updated_at = utc_now()
    if warning_count is not None:
        run.warning_count = warning_count
    run.error_message = error_message
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def save_market_data_result(
    session: Session,
    *,
    run_id: int,
    result: DailyDataResult,
) -> None:
    _add_market_data_result(session, run_id=run_id, result=result)
    session.commit()


def replace_market_data_for_run(
    session: Session,
    *,
    run_id: int,
    results: list[DailyDataResult],
) -> None:
    _delete_market_data_for_run(session, run_id)
    for result in results:
        _add_market_data_result(session, run_id=run_id, result=result)
    session.commit()


def _add_market_data_result(
    session: Session,
    *,
    run_id: int,
    result: DailyDataResult,
) -> None:
    retrieved_at = _naive_utc(result.retrieved_at or datetime.now(UTC))
    interface = result.interface or (
        result.bars[0].meta.interface if result.bars else ""
    )
    raw_record = RawMarketDataRecord(
        run_id=run_id,
        asset_id=result.request.asset_id,
        asset_type=result.request.asset_type,
        provider=result.provider,
        interface=interface,
        adjustment=result.request.adjustment,
        start_date=result.request.start,
        end_date=result.request.end,
        retrieved_at=retrieved_at,
        row_count=result.raw_row_count,
        rows=[dict(row) for row in result.raw_rows],
    )
    session.add(raw_record)

    for bar in result.bars:
        session.add(
            CleanMarketDataBarRecord(
                run_id=run_id,
                asset_id=bar.asset_id,
                asset_type=bar.asset_type,
                provider=bar.meta.provider,
                interface=bar.meta.interface,
                adjustment=bar.meta.adjustment,
                date=bar.date,
                open=_decimal_to_text(bar.open),
                high=_decimal_to_text(bar.high),
                low=_decimal_to_text(bar.low),
                close=_decimal_to_text(bar.close),
                adjusted_close=_decimal_to_text(bar.adjusted_close),
                nav=_decimal_to_text(bar.nav),
                accumulated_nav=_decimal_to_text(bar.accumulated_nav),
                volume=_decimal_to_text(bar.volume),
                tradable=bar.tradable,
                retrieved_at=_naive_utc(bar.meta.retrieved_at),
            )
        )

    for warning in result.warnings:
        session.add(
            DataWarningRecord(
                run_id=run_id,
                asset_id=warning.asset_id,
                date=warning.date,
                code=warning.code,
                message=warning.message,
            )
        )


def clear_market_data_for_run(session: Session, run_id: int) -> None:
    _delete_market_data_for_run(session, run_id)
    session.commit()


def _delete_market_data_for_run(session: Session, run_id: int) -> None:
    session.exec(
        delete(DataWarningRecord).where(col(DataWarningRecord.run_id) == run_id)
    )
    session.exec(
        delete(CleanMarketDataBarRecord).where(
            col(CleanMarketDataBarRecord.run_id) == run_id
        )
    )
    session.exec(
        delete(RawMarketDataRecord).where(col(RawMarketDataRecord.run_id) == run_id)
    )


def list_raw_market_data(session: Session, run_id: int) -> list[RawMarketDataRecord]:
    statement = (
        select(RawMarketDataRecord)
        .where(col(RawMarketDataRecord.run_id) == run_id)
        .order_by(col(RawMarketDataRecord.asset_id))
    )
    return list(session.exec(statement))


def list_clean_market_data_bars(
    session: Session,
    run_id: int,
) -> list[CleanMarketDataBarRecord]:
    statement = (
        select(CleanMarketDataBarRecord)
        .where(col(CleanMarketDataBarRecord.run_id) == run_id)
        .order_by(
            col(CleanMarketDataBarRecord.asset_id),
            col(CleanMarketDataBarRecord.date),
        )
    )
    return list(session.exec(statement))


def list_data_warnings(session: Session, run_id: int) -> list[DataWarningRecord]:
    statement = (
        select(DataWarningRecord)
        .where(col(DataWarningRecord.run_id) == run_id)
        .order_by(col(DataWarningRecord.asset_id), col(DataWarningRecord.date))
    )
    return list(session.exec(statement))


def _decimal_to_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
