"""remove_unique_constraint_from_liga_nombre

Revision ID: 42a74e929ea4
Revises: 004_equipo_unico_liga
Create Date: 2026-05-01 09:37:40.162164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42a74e929ea4'
down_revision: Union[str, Sequence[str], None] = '004_equipo_unico_liga'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove unique constraint from ligas.nombre column
    op.drop_constraint('ligas_nombre_key', 'ligas', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    # Add unique constraint back to ligas.nombre column
    op.create_unique_constraint('ligas_nombre_key', 'ligas', ['nombre'])
