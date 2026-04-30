from sqlmodel import Session, select

from foundlab.core.enums import AssetType, RunStatus
from foundlab.storage.models import AssetRecord, BacktestRunRecord, utc_now


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


def create_run(
    session: Session,
    *,
    name: str,
    asset_ids: list[str],
    strategy_name: str,
) -> BacktestRunRecord:
    run = BacktestRunRecord(
        name=name,
        asset_ids=asset_ids,
        strategy_name=strategy_name,
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
