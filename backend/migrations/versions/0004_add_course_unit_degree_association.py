
"""Adiciona a associação entre unidades curriculares e cursos (US-017).

Revision ID: 19eb6f032775
Revises: 0004_create_topico
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "19eb6f032775"
down_revision: str | None = "0004_create_topico"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("unidade_curricular") as batch_op:
        batch_op.add_column(
            sa.Column("curso_id", sa.Uuid(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_unidade_curricular_curso_id_curso",
            "curso",
            ["curso_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    with op.batch_alter_table("unidade_curricular") as batch_op:
        batch_op.drop_constraint(
            "fk_unidade_curricular_curso_id_curso",
            type_="foreignkey",
        )
        batch_op.drop_column("curso_id")
