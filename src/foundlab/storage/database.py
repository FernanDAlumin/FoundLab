from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./foundlab.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    from foundlab.storage.models import (
        AssetRecord,
        BacktestRunRecord,
        CleanMarketDataBarRecord,
        DataWarningRecord,
        RawMarketDataRecord,
    )

    _ = (
        AssetRecord,
        BacktestRunRecord,
        CleanMarketDataBarRecord,
        DataWarningRecord,
        RawMarketDataRecord,
    )
    SQLModel.metadata.create_all(engine)
    ensure_backtest_run_data_columns(engine)


def ensure_backtest_run_data_columns(db_engine: Engine) -> None:
    with db_engine.begin() as connection:
        inspector = inspect(connection)
        if "backtest_runs" not in inspector.get_table_names():
            return

        existing_columns = {
            column["name"]
            for column in inspector.get_columns("backtest_runs")
        }
        migration_statements = {
            "start_date": "alter table backtest_runs add column start_date date",
            "end_date": "alter table backtest_runs add column end_date date",
            "adjustment": (
                "alter table backtest_runs "
                "add column adjustment varchar(3) not null default 'qfq'"
            ),
        }
        for column_name, statement in migration_statements.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
