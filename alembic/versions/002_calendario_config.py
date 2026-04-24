"""Añadir configuración de calendario automático a liga_configuracion

Revision ID: 002_calendario_config
Revises: 001_liga_config
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_calendario_config'
down_revision = '001_liga_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Añadir columnas de configuración de calendario automático
    op.add_column('liga_configuracion', sa.Column('calendario_tipo', sa.String(20), nullable=True))
    op.add_column('liga_configuracion', sa.Column('calendario_fecha_inicio', sa.String(10), nullable=True))
    op.add_column('liga_configuracion', sa.Column('calendario_dias_partido', sa.Text(), nullable=True))
    op.add_column('liga_configuracion', sa.Column('calendario_hora', sa.String(5), nullable=True))


def downgrade() -> None:
    op.drop_column('liga_configuracion', 'calendario_hora')
    op.drop_column('liga_configuracion', 'calendario_dias_partido')
    op.drop_column('liga_configuracion', 'calendario_fecha_inicio')
    op.drop_column('liga_configuracion', 'calendario_tipo')
