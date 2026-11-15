"""Cria a tabela curso (US-015).

Revision ID: 0001_create_curso
Revises:
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_curso"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "curso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_curso")),
        sa.UniqueConstraint("codigo", name=op.f("uq_curso_codigo")),
    )


def downgrade() -> None:
    op.drop_table("curso")
