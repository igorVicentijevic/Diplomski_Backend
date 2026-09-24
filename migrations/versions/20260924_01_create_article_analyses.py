"""Create article analysis tables.

Revision ID: 20260924_01
Revises: 20260923_01
Create Date: 2026-09-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260924_01"
down_revision: str | Sequence[str] | None = "20260923_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "article_analyses",
        sa.Column("article_id", sa.String(length=255), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("article_id"),
    )
    op.create_table(
        "article_tone_analyses",
        sa.Column("article_id", sa.String(length=255), nullable=False),
        sa.Column("negative_percentage", sa.Float(), nullable=False),
        sa.Column("positive_percentage", sa.Float(), nullable=False),
        sa.Column("neutral_percentage", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["article_analyses.article_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("article_id"),
    )


def downgrade() -> None:
    op.drop_table("article_tone_analyses")
    op.drop_table("article_analyses")
