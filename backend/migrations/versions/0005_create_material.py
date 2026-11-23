"""Cria as tabelas material e versao_material (US-022).

Revision ID: 0005_create_material
Revises: 0004_create_topico
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_create_material"
down_revision: str | None = "0004_create_topico"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True, length=20)


def upgrade() -> None:
    op.create_table(
        "material",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descricao", sa.String(length=2000), nullable=True),
        sa.Column(
            "categoria",
            _enum(
                "categoria",
                "apontamentos",
                "apresentacao",
                "exercicios",
                "exame",
                "solucoes",
                "outro",
            ),
            nullable=False,
        ),
        sa.Column("origem", _enum("origem", "comunidade", "elearning"), nullable=False),
        sa.Column("ano_letivo", sa.String(length=9), nullable=True),
        sa.Column("estado", _enum("estado", "publicado", "removido"), nullable=False),
        sa.Column("topico_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=True),
        sa.Column(
            "publicado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("removido_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["topico_id"],
            ["topico.id"],
            name=op.f("fk_material_topico_id_topico"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_material")),
    )
    op.create_index(op.f("ix_material_autor_id"), "material", ["autor_id"], unique=False)
    op.create_index(op.f("ix_material_topico_id"), "material", ["topico_id"], unique=False)

    op.create_table(
        "versao_material",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("material_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("resumo_alteracao", sa.String(length=500), nullable=True),
        sa.Column("ficheiro_id", sa.Uuid(), nullable=False),
        sa.Column(
            "criada_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ficheiro_id"],
            ["stored_file.id"],
            name=op.f("fk_versao_material_ficheiro_id_stored_file"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["material.id"],
            name=op.f("fk_versao_material_material_id_material"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_versao_material")),
        sa.UniqueConstraint("ficheiro_id", name=op.f("uq_versao_material_ficheiro_id")),
        sa.UniqueConstraint("material_id", "numero", name="uq_versao_material_material_id_numero"),
    )
    op.create_index(
        op.f("ix_versao_material_material_id"), "versao_material", ["material_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_versao_material_material_id"), table_name="versao_material")
    op.drop_table("versao_material")
    op.drop_index(op.f("ix_material_topico_id"), table_name="material")
    op.drop_index(op.f("ix_material_autor_id"), table_name="material")
    op.drop_table("material")
