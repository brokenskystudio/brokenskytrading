from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app import main as main_module
from app.db.base import Base
from app.db.seed import seed_security_catalog
from app.models.security import Security


def test_seed_security_catalog_adds_missing_rows_to_existing_catalog() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as db:
        db.add(
            Security(
                symbol="AAPL",
                name="Custom Apple Name",
                exchange="NASDAQ",
                asset_type="equity",
                is_active=True,
                source="existing_database",
            )
        )
        db.commit()

        seed_security_catalog(db)

        assert db.scalar(select(Security.name).where(Security.symbol == "AAPL")) == "Custom Apple Name"
        assert db.scalar(select(Security.symbol).where(Security.symbol == "VTI")) == "VTI"

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_application_startup_seeds_security_catalog(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(main_module, "SessionLocal", session_factory)

    with TestClient(main_module.app):
        with session_factory() as db:
            assert db.scalar(select(Security.symbol).where(Security.symbol == "SCCO")) == "SCCO"

    Base.metadata.drop_all(engine)
    engine.dispose()