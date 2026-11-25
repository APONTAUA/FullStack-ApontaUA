"""merge academic periods and materials

Revision ID: c93fd1ba49a7
Revises: 0005_create_academic_periods, 0005_create_material
Create Date: 2026-11-24 00:38:41.198913

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'c93fd1ba49a7'
down_revision: str | Sequence[str] | None = ('0005_create_academic_periods', '0005_create_material')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
