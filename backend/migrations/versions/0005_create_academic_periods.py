"""Cria os anos letivos, semestres e associações com unidades curriculares (US-018).

Revision ID: 0005_create_academic_periods
Revises: 19eb6f032775
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_create_academic_periods"
down_revision: str | None = "19eb6f032775"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ano_letivo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ano_inicio", sa.Integer(), nullable=False),
        sa.Column("ano_fim", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ano_letivo")),
        sa.UniqueConstraint("ano_inicio", name=op.f("uq_ano_letivo_ano_inicio")),
        sa.CheckConstraint(
            "ano_fim = ano_inicio + 1",
            name=op.f("ck_ano_letivo_anos_consecutivos"),
        ),
    )

    op.create_table(
        "semestre",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("ano_letivo_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_semestre")),
        sa.ForeignKeyConstraint(
            ["ano_letivo_id"],
            ["ano_letivo.id"],
            name=op.f("fk_semestre_ano_letivo_id_ano_letivo"),
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "ano_letivo_id",
            "numero",
            name=op.f("uq_semestre_ano_letivo_numero"),
        ),
        sa.CheckConstraint(
            "numero IN (1, 2)",
            name=op.f("ck_semestre_numero_valido"),
        ),
    )

    op.create_table(
        "unidade_curricular_periodo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("unidade_curricular_id", sa.Uuid(), nullable=False),
        sa.Column("semestre_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_unidade_curricular_periodo"),
        ),
        sa.ForeignKeyConstraint(
            ["unidade_curricular_id"],
            ["unidade_curricular.id"],
            name=op.f("fk_unidade_curricular_periodo_unidade_curricular_id_unidade_curricular"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["semestre_id"],
            ["semestre.id"],
            name=op.f("fk_unidade_curricular_periodo_semestre_id_semestre"),
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "unidade_curricular_id",
            "semestre_id",
            name=op.f("uq_unidade_curricular_periodo"),
        ),
    )


def downgrade() -> None:
    op.drop_table("unidade_curricular_periodo")
    op.drop_table("semestre")
    op.drop_table("ano_letivo")
