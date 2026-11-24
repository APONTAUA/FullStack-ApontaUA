"""merge academic association and materials heads

Revision ID: 9e2cfd989132
Revises: 19eb6f032775, 0005_create_material
Create Date: 2026-11-24 00:01:56.405007

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '9e2cfd989132'
down_revision: str | Sequence[str] | None = ('19eb6f032775', '0005_create_material')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
