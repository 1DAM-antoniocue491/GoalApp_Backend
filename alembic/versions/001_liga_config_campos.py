"""add categoria to ligas and new fields to liga_configuracion

Revision ID: 001_liga_config
Revises:
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_liga_config'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Añadir columna categoria a ligas
    op.add_column('ligas', sa.Column('categoria', sa.String(50), nullable=True))

    # Añadir nuevas columnas a liga_configuracion
    op.add_column('liga_configuracion', sa.Column('min_equipos', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('liga_configuracion', sa.Column('min_convocados', sa.Integer(), nullable=False, server_default='14'))
    op.add_column('liga_configuracion', sa.Column('max_convocados', sa.Integer(), nullable=False, server_default='22'))
    op.add_column('liga_configuracion', sa.Column('min_plantilla', sa.Integer(), nullable=False, server_default='11'))
    op.add_column('liga_configuracion', sa.Column('max_plantilla', sa.Integer(), nullable=False, server_default='25'))
    op.add_column('liga_configuracion', sa.Column('minutos_partido', sa.Integer(), nullable=False, server_default='90'))
    op.add_column('liga_configuracion', sa.Column('max_partidos', sa.Integer(), nullable=False, server_default='30'))


def downgrade() -> None:
    op.drop_column('ligas', 'categoria')
    op.drop_column('liga_configuracion', 'max_partidos')
    op.drop_column('liga_configuracion', 'minutos_partido')
    op.drop_column('liga_configuracion', 'max_plantilla')
    op.drop_column('liga_configuracion', 'min_plantilla')
    op.drop_column('liga_configuracion', 'max_convocados')
    op.drop_column('liga_configuracion', 'min_convocados')
    op.drop_column('liga_configuracion', 'min_equipos')