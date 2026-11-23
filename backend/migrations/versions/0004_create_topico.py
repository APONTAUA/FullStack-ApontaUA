"""Cria a tabela topico (US-019).

Revision ID: 0004_create_topico
Revises: 0003_create_unidade_curricular
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_create_topico"
down_revision: str | None = "0003_create_unidade_curricular"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topico",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("uc_id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("descricao", sa.String(length=1000), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["uc_id"],
            ["unidade_curricular.id"],
            name=op.f("fk_topico_uc_id_unidade_curricular"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topico")),
        sa.UniqueConstraint("uc_id", "nome", name="uq_topico_uc_id_nome"),
    )
    op.create_index(op.f("ix_topico_uc_id"), "topico", ["uc_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_topico_uc_id"), table_name="topico")
    op.drop_table("topico")
