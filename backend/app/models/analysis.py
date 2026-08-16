from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    market_provider: Mapped[str] = mapped_column(String(100))
    metrics_json: Mapped[dict] = mapped_column(JSON)
    prompt_version: Mapped[str] = mapped_column(String(40), default="deterministic-v1")
