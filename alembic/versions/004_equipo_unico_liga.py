"""Implementar validación de equipos por liga

Revision ID: 004_equipo_unico_liga
Revises: 003_estado_jugador
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '004_equipo_unico_liga'
down_revision = '003_estado_jugador'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Quitar el índice único global del campo nombre
    op.drop_index('ix_equipos_nombre', table_name='equipos')
    
    # 2. Crear índice único compuesto (nombre + id_liga)
    op.create_index('idx_equipos_nombre_liga', 'equipos', ['nombre', 'id_liga'], unique=True)


def downgrade() -> None:
    # 1. Quitar el índice único compuesto
    op.drop_index('idx_equipos_nombre_liga', table_name='equipos')
    
    # 2. Recrear el índice único global del campo nombre
    op.create_index('ix_equipos_nombre', 'equipos', ['nombre'], unique=True)
