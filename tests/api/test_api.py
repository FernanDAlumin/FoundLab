from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from foundlab.api.main import create_app
from foundlab.storage.database import get_session


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


def test_create_asset_returns_created_asset() -> None:
    client = make_client()

    create_response = client.post(
        "/api/assets",
        json={
            "asset_id": "510300",
            "asset_type": "etf",
            "name": "沪深300ETF",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["asset_id"] == "510300"


def test_list_assets_returns_created_assets() -> None:
    client = make_client()

    client.post(
        "/api/assets",
        json={
            "asset_id": "510300",
            "asset_type": "etf",
            "name": "沪深300ETF",
        },
    )
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

    create_response = client.post(
        "/api/runs",
        json={
            "name": "ETF baseline",
            "asset_ids": ["510300"],
            "strategy_name": "daily_dca",
        },
    )

    assert create_response.status_code == 201
    run_id = create_response.json()["id"]
    assert isinstance(run_id, int)


def test_get_run_returns_pending_run() -> None:
    client = make_client()

    create_response = client.post(
        "/api/runs",
        json={
            "name": "ETF baseline",
            "asset_ids": ["510300"],
            "strategy_name": "daily_dca",
        },
    )
    run_id = create_response.json()["id"]

    get_response = client.get(f"/api/runs/{run_id}")

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "pending"
    assert get_response.json()["asset_ids"] == ["510300"]
