# tests/unit/conftest.py
"""
Fixtures especificas para tests unitarios.
Usa SQLite en memoria con TestClient de FastAPI.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.connection import Base
from app.main import app
from app.api.dependencies import get_db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.models.liga import Liga
from app.models.liga_configuracion import LigaConfiguracion
from app.models.equipo import Equipo
from app.models.jugador import Jugador
from app.models.partido import Partido
from app.models.notificacion import Notificacion
from app.api.services.usuario_service import hash_password
from datetime import datetime, timedelta, timezone


# ============================================================
# CONFIGURACION DE BASE DE DATOS EN MEMORIA
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Crea una base de datos en memoria para cada test unitario.
    Se crea y destruye despues de cada test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Cliente de prueba para hacer peticiones HTTP aisladas.
    Sobrescribe la dependencia get_db para usar la BD de test.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = {}


# ============================================================
# FIXTURES DE USUARIO Y AUTENTICACION
# ============================================================

@pytest.fixture
def usuario_ejemplo(db):
    """Crea un usuario de prueba."""
    usuario = Usuario(
        nombre="Usuario Test",
        email="test@email.com",
        contraseña_hash=hash_password("password123")
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def usuario2_ejemplo(db):
    """Crea un segundo usuario de prueba."""
    usuario = Usuario(
        nombre="Usuario Test 2",
        email="test2@email.com",
        contraseña_hash=hash_password("password123")
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def token_usuario(client, usuario_ejemplo):
    """Obtiene un token JWT para el usuario de prueba."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": usuario_ejemplo.email,
            "password": "password123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def headers_auth(token_usuario):
    """Headers con autorizacion Bearer."""
    return {"Authorization": f"Bearer {token_usuario}"}


# ============================================================
# FIXTURES DE ROLES
# ============================================================

@pytest.fixture
def rol_admin(db):
    """Crea un rol de administrador."""
    rol = Rol(nombre="admin", descripcion="Administrador del sistema")
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


@pytest.fixture
def rol_coach(db):
    """Crea un rol de entrenador."""
    rol = Rol(nombre="coach", descripcion="Entrenador de equipo")
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


@pytest.fixture
def rol_player(db):
    """Crea un rol de jugador."""
    rol = Rol(nombre="player", descripcion="Jugador")
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


@pytest.fixture
def usuario_admin(db, usuario_ejemplo, rol_admin, liga_ejemplo):
    """Crea un usuario con rol admin en una liga."""
    usuario_rol = UsuarioRol(
        id_usuario=usuario_ejemplo.id_usuario,
        id_rol=rol_admin.id_rol,
        id_liga=liga_ejemplo.id_liga
    )
    db.add(usuario_rol)
    db.commit()
    db.refresh(usuario_ejemplo)
    return usuario_ejemplo


@pytest.fixture
def token_admin(client, usuario_admin):
    """Token JWT para usuario con rol admin."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": usuario_admin.email,
            "password": "password123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def headers_admin(token_admin):
    """Headers con autorizacion Bearer para admin."""
    return {"Authorization": f"Bearer {token_admin}"}


# ============================================================
# FIXTURES DE LIGA
# ============================================================

@pytest.fixture
def liga_ejemplo(db):
    """Crea una liga de prueba."""
    liga = Liga(
        nombre="Liga Test",
        temporada="2024-2025",
        activa=True
    )
    db.add(liga)
    db.commit()
    db.refresh(liga)
    return liga


@pytest.fixture
def liga2_ejemplo(db):
    """Crea una segunda liga de prueba."""
    liga = Liga(
        nombre="Liga Test 2",
        temporada="2024-2025",
        activa=True
    )
    db.add(liga)
    db.commit()
    db.refresh(liga)
    return liga


@pytest.fixture
def liga_configuracion_ejemplo(db, liga_ejemplo):
    """Crea una configuracion de liga de prueba."""
    from datetime import time
    configuracion = LigaConfiguracion(
        id_liga=liga_ejemplo.id_liga,
        hora_partidos=time(17, 0),
        max_equipos=20,
        min_partidos_entre_equipos=2,
        min_convocados=14,
        max_convocados=22,
        min_plantilla=11
    )
    db.add(configuracion)
    db.commit()
    db.refresh(configuracion)
    return configuracion


# ============================================================
# FIXTURES DE EQUIPO
# ============================================================

@pytest.fixture
def equipo_ejemplo(db, liga_ejemplo, usuario_ejemplo, usuario2_ejemplo):
    """Crea un equipo de prueba."""
    equipo = Equipo(
        nombre="Equipo Test",
        id_liga=liga_ejemplo.id_liga,
        id_entrenador=usuario_ejemplo.id_usuario,
        id_delegado=usuario2_ejemplo.id_usuario
    )
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo


@pytest.fixture
def equipo2_ejemplo(db, liga_ejemplo, usuario_ejemplo, usuario2_ejemplo):
    """Crea un segundo equipo de prueba."""
    equipo = Equipo(
        nombre="Equipo Test 2",
        id_liga=liga_ejemplo.id_liga,
        id_entrenador=usuario_ejemplo.id_usuario,
        id_delegado=usuario2_ejemplo.id_usuario
    )
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo


# ============================================================
# FIXTURES DE JUGADOR
# ============================================================

@pytest.fixture
def jugador_ejemplo(db, usuario_ejemplo, equipo_ejemplo):
    """Crea un jugador de prueba."""
    jugador = Jugador(
        id_usuario=usuario_ejemplo.id_usuario,
        id_equipo=equipo_ejemplo.id_equipo,
        posicion="Delantero",
        dorsal=10,
        activo=True
    )
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    return jugador


# ============================================================
# FIXTURES DE PARTIDO
# ============================================================

@pytest.fixture
def partido_ejemplo(db, liga_ejemplo, equipo_ejemplo, equipo2_ejemplo):
    """Crea un partido de prueba."""
    partido = Partido(
        id_liga=liga_ejemplo.id_liga,
        id_equipo_local=equipo_ejemplo.id_equipo,
        id_equipo_visitante=equipo2_ejemplo.id_equipo,
        fecha=datetime.now(timezone.utc) + timedelta(days=7),
        estado="programado"
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    return partido


# ============================================================
# FIXTURES DE NOTIFICACION
# ============================================================

@pytest.fixture
def notificacion_ejemplo(db, usuario_ejemplo):
    """Crea una notificacion de prueba."""
    notificacion = Notificacion(
        id_usuario=usuario_ejemplo.id_usuario,
        mensaje="Notificacion de prueba",
        leida=False
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


# ============================================================
# FIXTURES DE DATOS CON IDS (para crear entidades)
# ============================================================

@pytest.fixture
def datos_equipo_nuevo(liga_ejemplo, usuario_ejemplo, usuario2_ejemplo):
    """Datos para crear un nuevo equipo."""
    return {
        "nombre": "Nuevo Equipo",
        "id_liga": liga_ejemplo.id_liga,
        "id_entrenador": usuario_ejemplo.id_usuario,
        "id_delegado": usuario2_ejemplo.id_usuario
    }