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
    # MySQL - Configuración optimizada para Render
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,  # Verificar que la conexión esté viva antes de usar
        pool_recycle=300,     # Reciclar conexiones cada 5 minutos (más agresivo para Render)
        pool_size=5,          # Pool más pequeño para Render (5 conexiones base)
        max_overflow=5,       # Hasta 10 conexiones totales en pico
        pool_timeout=30,      # Timeout de 30s para obtener conexión del pool
        connect_args={
            "connect_timeout": 10,  # Timeout de conexión de 10s
            "read_timeout": 30,     # Timeout de lectura de 30s
            "write_timeout": 30      # Timeout de escritura de 30s
        }
    )

# Crea la fábrica de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()
