from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.api.portfolios import holdings_router, market_data_router, router as portfolios_router
from app.db.base import Base
from app.db.seed import seed_security_catalog
from app.db.session import SessionLocal, check_database, engine, get_db
from app.models import Holding, Portfolio


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_security_catalog(db)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    del db
    check_database()
    return {"status": "ok", "database": "sqlite" if settings.database_url.startswith("sqlite") else "configured"}


app.include_router(portfolios_router)
app.include_router(holdings_router)
app.include_router(market_data_router)
