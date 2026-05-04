"""add codigo to invitaciones

Revision ID: 005_invitacion_codigo
Revises: 42a74e929ea4
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '005_invitacion_codigo'
down_revision = '42a74e929ea4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Añadir columna codigo a invitaciones
    op.add_column('invitaciones', sa.Column('codigo', sa.String(8), nullable=True))

    # Crear índice único para el campo codigo
    op.create_index('ix_invitaciones_codigo', 'invitaciones', ['codigo'], unique=True)


def downgrade() -> None:
    # Eliminar índice único
    op.drop_index('ix_invitaciones_codigo', 'invitaciones')

    # Eliminar columna codigo
    op.drop_column('invitaciones', 'codigo')
