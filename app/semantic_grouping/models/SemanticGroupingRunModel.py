from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.Base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class SemanticGroupingRunModel(Base):
    __tablename__ = "semantic_grouping_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(255))
    threshold: Mapped[float] = mapped_column(Float)
    boundary_min: Mapped[float] = mapped_column(Float)
    boundary_max: Mapped[float] = mapped_column(Float)
    candidate_window_hours: Mapped[int] = mapped_column(Integer)
    article_count: Mapped[int] = mapped_column(Integer)
    pair_count: Mapped[int] = mapped_column(Integer)
    positive_pair_count: Mapped[int] = mapped_column(Integer)
    boundary_pair_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
