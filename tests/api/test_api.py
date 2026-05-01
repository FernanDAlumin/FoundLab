from collections.abc import Generator

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import foundlab.api.main as api_main
import foundlab.api.routes.runs as runs_route
from foundlab.api.main import create_app
from foundlab.core.enums import RunStatus
from foundlab.storage.database import get_session
from foundlab.worker.jobs import JobResult

ASSET_PAYLOAD = {
    "asset_id": "510300",
    "asset_type": "etf",
    "name": "沪深300ETF",
}

RUN_PAYLOAD = {
    "name": "ETF baseline",
    "asset_ids": ["510300"],
    "strategy_name": "daily_dca",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "adjustment": "qfq",
}


def make_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def test_health_returns_ok() -> None:
    client = make_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "foundlab-api"}


def test_app_lifespan_creates_db_tables(monkeypatch: MonkeyPatch) -> None:
    calls = 0

    def fake_create_db_and_tables() -> None:
        nonlocal calls
        calls += 1

    monkeypatch.setattr(api_main, "create_db_and_tables", fake_create_db_and_tables)

    with TestClient(create_app()):
        pass

    assert calls == 1


def test_create_asset_returns_created_asset() -> None:
    client = make_client()

    create_response = client.post("/api/assets", json=ASSET_PAYLOAD)

    assert create_response.status_code == 201
    assert create_response.json() == {
        "id": 1,
        "asset_id": "510300",
        "asset_type": "etf",
        "name": "沪深300ETF",
    }


def test_list_assets_returns_created_assets() -> None:
    client = make_client()

    client.post("/api/assets", json=ASSET_PAYLOAD)
    list_response = client.get("/api/assets")

    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            "id": 1,
            "asset_id": "510300",
            "asset_type": "etf",
            "name": "沪深300ETF",
        }
    ]


def test_create_run_returns_id() -> None:
    client = make_client()

    create_response = client.post("/api/runs", json=RUN_PAYLOAD)

    assert create_response.status_code == 201
    response_json = create_response.json()
    run_id = response_json["id"]
    assert isinstance(run_id, int)
    assert response_json == {
        "id": run_id,
        "name": "ETF baseline",
        "asset_ids": ["510300"],
        "strategy_name": "daily_dca",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "adjustment": "qfq",
        "status": "pending",
        "warning_count": 0,
        "error_message": None,
    }


def test_get_run_returns_pending_run() -> None:
    client = make_client()

    create_response = client.post("/api/runs", json=RUN_PAYLOAD)
    run_id = create_response.json()["id"]

    get_response = client.get(f"/api/runs/{run_id}")

    assert get_response.status_code == 200
    assert get_response.json() == {
        "id": run_id,
        "name": "ETF baseline",
        "asset_ids": ["510300"],
        "strategy_name": "daily_dca",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "adjustment": "qfq",
        "status": "pending",
        "warning_count": 0,
        "error_message": None,
    }


def test_get_run_returns_404_when_run_does_not_exist() -> None:
    client = make_client()

    response = client.get("/api/runs/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}


def test_prepare_run_data_returns_job_result(monkeypatch: MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_run_data_preparation_job(
        session: Session,
        run_id: int,
    ) -> JobResult:
        calls.append(run_id)
        return JobResult(
            run_id=run_id,
            status=RunStatus.SUCCEEDED_WITH_WARNINGS,
            warning_count=1,
            bar_count=3,
        )

    monkeypatch.setattr(
        runs_route,
        "run_data_preparation_job",
        fake_run_data_preparation_job,
    )
    client = make_client()

    response = client.post("/api/runs/7/prepare-data")

    assert response.status_code == 200
    assert calls == [7]
    assert response.json() == {
        "run_id": 7,
        "status": "succeeded_with_warnings",
        "warning_count": 1,
        "bar_count": 3,
        "error_message": None,
    }
