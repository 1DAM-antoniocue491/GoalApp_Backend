from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config import settings

# ============================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ============================================================

# Motor de base de datos con configuración desde settings
# Configuración diferente para SQLite vs MySQL
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite no soporta pool_pre_ping ni pool_recycle
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False}  # Necesario para SQLite en FastAPI
    )
else:
    # MySQL
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=3600,  # Reciclar conexiones cada hora
        pool_size=10,  # Número de conexiones en el pool
        max_overflow=20  # Conexiones adicionales si se agota el pool
    )

# Crea la fábrica de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()
