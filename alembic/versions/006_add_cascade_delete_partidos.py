"""Añadir ON DELETE CASCADE a partidos.id_equipo_local y partidos.id_equipo_visitante

Revision ID: 006_cascade_partidos
Revises: 005_invitacion_codigo
Create Date: 2026-05-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '006_cascade_partidos'
down_revision = '005_invitacion_codigo'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Para PostgreSQL
    # Eliminar y recrear foreign key para id_equipo_local con ON DELETE CASCADE
    op.drop_constraint('partidos_id_equipo_local_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_equipo_local_fkey',
        'partidos',
        'equipos',
        ['id_equipo_local'],
        ['id_equipo'],
        ondelete='CASCADE'
    )

    # Eliminar y recrear foreign key para id_equipo_visitante con ON DELETE CASCADE
    op.drop_constraint('partidos_id_equipo_visitante_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_equipo_visitante_fkey',
        'partidos',
        'equipos',
        ['id_equipo_visitante'],
        ['id_equipo'],
        ondelete='CASCADE'
    )

    # También añadir CASCADE a id_liga e id_jornada para consistencia
    op.drop_constraint('partidos_id_liga_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_liga_fkey',
        'partidos',
        'ligas',
        ['id_liga'],
        ['id_liga'],
        ondelete='CASCADE'
    )

    op.drop_constraint('partidos_id_jornada_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_jornada_fkey',
        'partidos',
        'jornadas',
        ['id_jornada'],
        ['id_jornada'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Revertir a foreign keys sin CASCADE
    op.drop_constraint('partidos_id_jornada_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_jornada_fkey',
        'partidos',
        'jornadas',
        ['id_jornada'],
        ['id_jornada']
    )

    op.drop_constraint('partidos_id_liga_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_liga_fkey',
        'partidos',
        'ligas',
        ['id_liga'],
        ['id_liga']
    )

    op.drop_constraint('partidos_id_equipo_visitante_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_equipo_visitante_fkey',
        'partidos',
        'equipos',
        ['id_equipo_visitante'],
        ['id_equipo']
    )

    op.drop_constraint('partidos_id_equipo_local_fkey', 'partidos', type_='foreignkey')
    op.create_foreign_key(
        'partidos_id_equipo_local_fkey',
        'partidos',
        'equipos',
        ['id_equipo_local'],
        ['id_equipo']
    )
