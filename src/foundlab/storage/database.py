from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./foundlab.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    from foundlab.storage.models import AssetRecord, BacktestRunRecord

    _ = (AssetRecord, BacktestRunRecord)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
