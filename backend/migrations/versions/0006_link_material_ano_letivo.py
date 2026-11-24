"""Liga materiais aos anos letivos (US-018)."""

import sqlalchemy as sa
from alembic import op

revision = "0006_link_material_ano_letivo"
down_revision = "c93fd1ba49a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("material") as batch:
        batch.add_column(
            sa.Column("ano_letivo_id", sa.Uuid(), nullable=True)
        )
        batch.create_foreign_key(
            "fk_material_ano_letivo_id_ano_letivo",
            "ano_letivo",
            ["ano_letivo_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index(
            "ix_material_ano_letivo_id",
            ["ano_letivo_id"],
        )

    # Associar materiais antigos sem apagar os seus metadados.
    anos = sa.table(
        "ano_letivo",
        sa.column("id", sa.Uuid()),
        sa.column("ano_inicio", sa.Integer()),
        sa.column("ano_fim", sa.Integer()),
    )
    materiais = sa.table(
        "material",
        sa.column("ano_letivo", sa.String(9)),
        sa.column("ano_letivo_id", sa.Uuid()),
    )

    descricao_ano = (
        sa.cast(anos.c.ano_inicio, sa.String())
        + sa.literal("/")
        + sa.cast(anos.c.ano_fim, sa.String())
    )

    ano_id = (
        sa.select(anos.c.id)
        .where(materiais.c.ano_letivo == descricao_ano)
        .scalar_subquery()
    )

    op.get_bind().execute(
        sa.update(materiais)
        .where(materiais.c.ano_letivo.is_not(None))
        .values(ano_letivo_id=ano_id)
    )


def downgrade() -> None:
    with op.batch_alter_table("material") as batch:
        batch.drop_index("ix_material_ano_letivo_id")
        batch.drop_constraint(
            "fk_material_ano_letivo_id_ano_letivo",
            type_="foreignkey",
        )
        batch.drop_column("ano_letivo_id")
