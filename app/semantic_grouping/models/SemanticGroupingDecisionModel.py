from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.Base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class SemanticGroupingDecisionModel(Base):
    __tablename__ = "semantic_grouping_decisions"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "left_article_id",
            "right_article_id",
            name="uq_semantic_grouping_decision_pair",
        ),
        Index(
            "ix_semantic_grouping_decisions_boundary",
            "is_boundary_candidate",
            "similarity",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey(
            "semantic_grouping_runs.id",
            ondelete="CASCADE",
        ),
        index=True,
    )
    left_article_id: Mapped[str] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True,
    )
    right_article_id: Mapped[str] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True,
    )
    similarity: Mapped[float] = mapped_column(Float)
    predicted_same_event: Mapped[bool] = mapped_column(Boolean)
    proposed_group_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    is_boundary_candidate: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
