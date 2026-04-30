from collections.abc import Generator

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import foundlab.api.main as api_main
from foundlab.api.main import create_app
from foundlab.storage.database import get_session

ASSET_PAYLOAD = {
    "asset_id": "510300",
    "asset_type": "etf",
    "name": "沪深300ETF",
}

RUN_PAYLOAD = {
    "name": "ETF baseline",
    "asset_ids": ["510300"],
    "strategy_name": "daily_dca",
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
        "status": "pending",
        "warning_count": 0,
        "error_message": None,
    }


def test_get_run_returns_404_when_run_does_not_exist() -> None:
    client = make_client()

    response = client.get("/api/runs/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}
