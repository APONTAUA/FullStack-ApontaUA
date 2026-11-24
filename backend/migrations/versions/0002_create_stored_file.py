"""Create file metadata table."""

import sqlalchemy as sa
from alembic import op

revision = "0002_stored_file"
down_revision = "0001_create_curso"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stored_file",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stored_file")),
        sa.UniqueConstraint("object_key", name=op.f("uq_stored_file_object_key")),
    )


def downgrade() -> None:
    op.drop_table("stored_file")
