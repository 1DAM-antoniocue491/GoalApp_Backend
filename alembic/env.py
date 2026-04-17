from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Importar configuración de la aplicación
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database.connection import Base

# Importar todos los modelos para que Alembic los detecte
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.models.usuario_sigue_liga import UsuarioSigueLiga
from app.models.liga import Liga
from app.models.liga_configuracion import LigaConfiguracion
from app.models.equipo import Equipo
from app.models.jugador import Jugador
from app.models.partido import Partido
from app.models.evento_partido import EventoPartido
from app.models.formacion import Formacion
from app.models.formacion_equipo import FormacionEquipo
from app.models.formacion_partido import FormacionPartido
from app.models.posicion_formacion import PosicionFormacion
from app.models.alineacion_partido import AlineacionPartido
from app.models.notificacion import Notificacion
from app.models.convocatoria_partido import ConvocatoriaPartido
from app.models.token_recuperacion import TokenRecuperacion

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Sobrescribir la URL de la base de datos con la configuración de la app
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario, we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()