from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config import settings

# ============================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ============================================================

# Motor de base de datos con configuración desde settings
# Configuración diferente según el tipo de base de datos
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite no soporta pool_pre_ping ni pool_recycle
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False}  # Necesario para SQLite en FastAPI
    )
elif settings.DATABASE_URL.startswith("postgresql"):
    # PostgreSQL - Configuración optimizada para producción (Render)
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,      # Verificar que la conexión esté viva antes de usar
        pool_recycle=600,        # Reciclar conexiones cada 10 minutos (evita timeout de Render)
        pool_size=10,            # 10 conexiones base (aumentado para producción)
        max_overflow=10,         # Hasta 20 conexiones totales en pico
        pool_timeout=60,         # Timeout de 60s para obtener conexión del pool
        connect_args={
            "connect_timeout": 10,  # Timeout de conexión de 10s
            "options": "-c statement_timeout=30000"  # Timeout de queries de 30s
        }
    )
else:
    # Fallback para otros motores de base de datos
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
    )

# Crea la fábrica de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()