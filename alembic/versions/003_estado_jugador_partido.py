"""Añadir tabla estado_jugador_partido y campo id_jugador_sale en eventos_partido

Revision ID: 003_estado_jugador
Revises: 002_calendario_config
Create Date: 2026-04-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_estado_jugador'
down_revision = '002_calendario_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Crear tabla estado_jugador_partido
    op.create_table(
        'estado_jugador_partido',
        sa.Column('id_estado', sa.Integer(), nullable=False),
        sa.Column('id_partido', sa.Integer(), nullable=False),
        sa.Column('id_jugador', sa.Integer(), nullable=False),
        sa.Column('id_equipo', sa.Integer(), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False),
        sa.Column('minuto_entrada', sa.Integer(), nullable=True),
        sa.Column('minuto_salida', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['id_partido'], ['partidos.id_partido'], ),
        sa.ForeignKeyConstraint(['id_jugador'], ['jugadores.id_jugador'], ),
        sa.ForeignKeyConstraint(['id_equipo'], ['equipos.id_equipo'], ),
        sa.PrimaryKeyConstraint('id_estado')
    )

    # 2. Añadir índice para consultas rápidas por partido y jugador
    op.create_index('ix_estado_jugador_partido_id_partido', 'estado_jugador_partido', ['id_partido'])
    op.create_index('ix_estado_jugador_partido_id_jugador', 'estado_jugador_partido', ['id_jugador'])
    op.create_index('ix_estado_jugador_partido_id_equipo', 'estado_jugador_partido', ['id_equipo'])

    # 3. Añadir columna id_jugador_sale a eventos_partido (para sustituciones)
    op.add_column('eventos_partido', sa.Column('id_jugador_sale', sa.Integer(), nullable=True))

    # 4. Crear foreign key para id_jugador_sale
    op.create_foreign_key(
        'fk_eventos_jugador_sale',
        'eventos_partido',
        'jugadores',
        ['id_jugador_sale'],
        ['id_jugador']
    )


def downgrade() -> None:
    # 1. Eliminar foreign key de id_jugador_sale
    op.drop_constraint('fk_eventos_jugador_sale', 'eventos_partido', type_='foreignkey')

    # 2. Eliminar columna id_jugador_sale de eventos_partido
    op.drop_column('eventos_partido', 'id_jugador_sale')

    # 3. Eliminar índices
    op.drop_index('ix_estado_jugador_partido_id_equipo', table_name='estado_jugador_partido')
    op.drop_index('ix_estado_jugador_partido_id_jugador', table_name='estado_jugador_partido')
    op.drop_index('ix_estado_jugador_partido_id_partido', table_name='estado_jugador_partido')

    # 4. Eliminar tabla estado_jugador_partido
    op.drop_table('estado_jugador_partido')
