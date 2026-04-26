# app/main.py
"""
Punto de entrada principal de la aplicación FastAPI.
Configura la aplicación, middlewares, routers y eventos de ciclo de vida.
"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database.connection import engine, Base

# Importar todos los modelos primero para registrar las clases en SQLAlchemy
# Esto evita errores de resolución de nombres en relaciones con string references
from .models import __all__ as models_all  # noqa: F401 - Registra todos los modelos

# Importar modelos individualmente para crear las tablas (necesario para metadata)
from .models import (
    usuario,
    rol,
    liga,
    liga_configuracion,
    equipo,
    jugador,
    partido,
    evento_partido,
    notificacion,
    convocatoria_partido,
    jornada,
    alineacion_partido,
    token_recuperacion,
    invitacion,
    usuario_sigue_liga,
)

# Importar todos los routers
from .api.routers import (
    auth,
    usuarios,
    roles,
    equipos,
    jugadores,
    ligas,
    liga_configuracion,
    partidos,
    eventos,
    notificaciones,
    imagenes,
    convocatorias,
    alineaciones,
    tokens_recuperacion,
    invitaciones,
    public,
    estadisticas
)


# ============================================================
# EVENTOS DE CICLO DE VIDA
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Se ejecuta al inicio y al cierre del servidor.
    """
    # Startup: Crear tablas si no existen
    print("[INFO] Iniciando aplicación...")
    # Mostrar URL de base de datos (ocultar credenciales si contiene @)
    db_url = settings.DATABASE_URL
    if '@' in db_url:
        # Base de datos con credenciales: mostrar solo host/db
        print(f"[INFO] Conectando a base de datos: {db_url.split('@')[1]}")
    else:
        # SQLite: mostrar toda la URL (no tiene credenciales)
        print(f"[INFO] Conectando a base de datos: {db_url}")

    # Crear todas las tablas definidas en los modelos
    # NOTA: En producción, usar Alembic en lugar de esto
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tablas de base de datos verificadas")
    except Exception as e:
        # Si las tablas ya existen o hay error de índices, continuar
        # Esto es común en hosts con límites de almacenamiento
        print(f"[WARN] No se pudieron verificar todas las tablas/índices: {e}")
        print("[INFO] Continuando con las tablas existentes...")

    yield

    # Shutdown: Cerrar conexiones
    print("[INFO] Cerrando aplicación...")
    engine.dispose()
    print("[OK] Conexiones de base de datos cerradas")


# ============================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="API REST para gestión de ligas de fútbol amateur",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json",
    lifespan=lifespan
)


# ============================================================
# MIDDLEWARE DE CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTRO DE ROUTERS
# ============================================================

# Autenticación
app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["Autenticación"]
)

# Usuarios y roles
app.include_router(
    usuarios.router,
    prefix="/api/v1",
    tags=["Usuarios"]
)

app.include_router(
    roles.router,
    prefix="/api/v1",
    tags=["Roles"]
)

# Ligas, equipos y jugadores
app.include_router(
    ligas.router,
    prefix="/api/v1",
    tags=["Ligas"]
)

app.include_router(
    liga_configuracion.router,
    prefix="/api/v1",
    tags=["Configuración de Liga"]
)

app.include_router(
    equipos.router,
    prefix="/api/v1",
    tags=["Equipos"]
)

app.include_router(
    jugadores.router,
    prefix="/api/v1",
    tags=["Jugadores"]
)

# Partidos y eventos
app.include_router(
    partidos.router,
    prefix="/api/v1",
    tags=["Partidos"]
)

app.include_router(
    eventos.router,
    prefix="/api/v1",
    tags=["Eventos"]
)

# Convocatorias
app.include_router(
    convocatorias.router,
    prefix="/api/v1",
    tags=["Convocatorias"]
)

# Alineaciones
app.include_router(
    alineaciones.router,
    prefix="/api/v1",
    tags=["Alineaciones"]
)

# Tokens de Recuperación (administración)
app.include_router(
    tokens_recuperacion.router,
    prefix="/api/v1",
    tags=["Tokens de Recuperación"]
)

# Invitaciones
app.include_router(
    invitaciones.router,
    prefix="/api/v1",
    tags=["Invitaciones"]
)

app.include_router(
    notificaciones.router,
    prefix="/api/v1",
    tags=["Notificaciones"]
)

# Imágenes
app.include_router(
    imagenes.router,
    prefix="/api/v1",
    tags=["Imágenes"]
)

# Endpoints públicos (sin autenticación)
app.include_router(
    public.router,
    prefix="/api/v1",
    tags=["Público"]
)

# Estadísticas
app.include_router(
    estadisticas.router,
    prefix="/api/v1",
    tags=["Estadísticas"]
)


# ============================================================
# ENDPOINTS DE SALUD Y RAÍZ
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    """
    return {
        "mensaje": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.API_VERSION,
        "entorno": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint para verificar el estado de salud de la API.
    Útil para monitoring y balanceadores de carga.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


# ============================================================
# PUNTO DE ENTRADA PARA EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║  {settings.APP_NAME:^55}  ║
    ║  Version: {settings.API_VERSION:^48}  ║
    ║  Entorno: {settings.ENVIRONMENT:^48}  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
