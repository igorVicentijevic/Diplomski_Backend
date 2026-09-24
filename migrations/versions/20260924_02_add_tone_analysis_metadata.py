"""Add tone analysis reuse metadata.

Revision ID: 20260924_02
Revises: 20260924_01
Create Date: 2026-09-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260924_02"
down_revision: str | Sequence[str] | None = "20260924_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "article_tone_analyses",
        sa.Column("input_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "article_tone_analyses",
        sa.Column("provider", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "article_tone_analyses",
        sa.Column("model_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "article_tone_analyses",
        sa.Column(
            "prompt_version",
            sa.String(length=64),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("article_tone_analyses", "prompt_version")
    op.drop_column("article_tone_analyses", "model_name")
    op.drop_column("article_tone_analyses", "provider")
    op.drop_column("article_tone_analyses", "input_hash")
