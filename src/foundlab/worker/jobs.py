from dataclasses import dataclass

from sqlmodel import Session

from foundlab.core.data.akshare_provider import AkShareProvider
from foundlab.core.data.pipeline import fetch_and_clean_daily_data
from foundlab.core.data.provider import MarketDataProvider, ProviderRequest
from foundlab.core.enums import RunStatus
from foundlab.storage.repositories import (
    get_assets_by_ids,
    get_run,
    replace_market_data_for_run,
    update_run_status,
)


@dataclass(frozen=True)
class JobResult:
    run_id: int
    status: RunStatus
    warning_count: int
    bar_count: int = 0
    error_message: str | None = None


def run_foundation_job(session: Session, run_id: int) -> JobResult:
    run = get_run(session, run_id)
    if run is None:
        return JobResult(
            run_id=run_id,
            status=RunStatus.FAILED,
            warning_count=0,
            error_message=f"Run {run_id} not found",
        )

    update_run_status(session, run, status=RunStatus.RUNNING)
    updated = update_run_status(session, run, status=RunStatus.SUCCEEDED, warning_count=0)
    return JobResult(
        run_id=updated.id or run_id,
        status=updated.status,
        warning_count=updated.warning_count,
        error_message=updated.error_message,
    )


def run_data_preparation_job(
    session: Session,
    run_id: int,
    *,
    provider: MarketDataProvider | None = None,
) -> JobResult:
    run = get_run(session, run_id)
    if run is None:
        return JobResult(
            run_id=run_id,
            status=RunStatus.FAILED,
            warning_count=0,
            error_message=f"Run {run_id} not found",
        )

    if run.start_date is None or run.end_date is None:
        updated = update_run_status(
            session,
            run,
            status=RunStatus.FAILED,
            error_message="Run must define start_date and end_date before fetching data",
        )
        return JobResult(
            run_id=updated.id or run_id,
            status=updated.status,
            warning_count=updated.warning_count,
            error_message=updated.error_message,
        )

    update_run_status(session, run, status=RunStatus.RUNNING)
    data_provider = provider or AkShareProvider()
    assets = get_assets_by_ids(session, run.asset_ids)
    found_asset_ids = {asset.asset_id for asset in assets}
    missing_asset_ids = [
        asset_id for asset_id in run.asset_ids if asset_id not in found_asset_ids
    ]
    if missing_asset_ids:
        updated = update_run_status(
            session,
            run,
            status=RunStatus.FAILED,
            error_message=f"Run references unknown assets: {', '.join(missing_asset_ids)}",
        )
        return JobResult(
            run_id=updated.id or run_id,
            status=updated.status,
            warning_count=updated.warning_count,
            error_message=updated.error_message,
        )

    warning_count = 0
    bar_count = 0
    results = []
    try:
        for asset in assets:
            result = fetch_and_clean_daily_data(
                provider=data_provider,
                request=ProviderRequest(
                    asset_id=asset.asset_id,
                    asset_type=asset.asset_type,
                    start=run.start_date,
                    end=run.end_date,
                    adjustment=run.adjustment,
                ),
            )
            warning_count += result.warning_count
            bar_count += len(result.bars)
            results.append(result)
    except Exception as exc:
        updated = update_run_status(
            session,
            run,
            status=RunStatus.FAILED,
            warning_count=warning_count,
            error_message=str(exc),
        )
        return JobResult(
            run_id=updated.id or run_id,
            status=updated.status,
            warning_count=updated.warning_count,
            bar_count=bar_count,
            error_message=updated.error_message,
        )
    replace_market_data_for_run(session, run_id=run_id, results=results)
    final_status = (
        RunStatus.SUCCEEDED_WITH_WARNINGS
        if warning_count
        else RunStatus.SUCCEEDED
    )
    updated = update_run_status(
        session,
        run,
        status=final_status,
        warning_count=warning_count,
    )
    return JobResult(
        run_id=updated.id or run_id,
        status=updated.status,
        warning_count=updated.warning_count,
        bar_count=bar_count,
        error_message=updated.error_message,
    )
