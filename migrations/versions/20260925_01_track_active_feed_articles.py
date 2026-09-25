"""Track active RSS feed articles.

Revision ID: 20260925_01
Revises: 20260924_02
Create Date: 2026-09-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260925_01"
down_revision: str | Sequence[str] | None = "20260924_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("source_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "articles",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )

    op.execute(
        sa.text(
            "UPDATE articles "
            "SET source_id = CASE "
            "WHEN id ~ '-[0-9a-f]{64}$' "
            "THEN left(id, length(id) - 65) "
            "ELSE 'legacy' "
            "END, "
            "last_seen_at = updated_at"
        )
    )

    op.alter_column(
        "articles",
        "source_id",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.alter_column(
        "articles",
        "last_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_index(
        op.f("ix_articles_source_id"),
        "articles",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_articles_source_id"),
        table_name="articles",
    )
    op.drop_column("articles", "is_active")
    op.drop_column("articles", "last_seen_at")
    op.drop_column("articles", "source_id")
