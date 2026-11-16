
"""Cria a tabela unidade_curricular (US-016).

Revision ID: 0002_create_unidade_curricular
Revises: 0001_create_curso
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_unidade_curricular"
down_revision: str | None = "0001_create_curso"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "unidade_curricular",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_unidade_curricular")),
        sa.UniqueConstraint("codigo", name=op.f("uq_unidade_curricular_codigo")),
    )


def downgrade() -> None:
    op.drop_table("unidade_curricular")
