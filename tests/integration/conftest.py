# tests/integration/conftest.py
"""
Fixtures especificas para tests de integracion.
Se conecta a la API remota desplegada.
"""
import pytest
import os
import requests
from typing import Optional


# ============================================================
# CONFIGURACION DE CONEXION REMOTA
# ============================================================

@pytest.fixture(scope="session")
def api_base_url():
    """
    URL base de la API remota.
    Se lee de: --api-url > INTEGRATION_API_URL > default
    """
    url = os.getenv(
        "INTEGRATION_API_URL",
        "http://localhost:8000/api/v1"
    )
    return url.rstrip("/")


@pytest.fixture(scope="session")
def api_client(api_base_url):
    """
    Cliente HTTP para la API remota.
    Usa la libreria requests directamente.
    """
    class APIClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
            self.session = requests.Session()
            self.token: Optional[str] = None

        def login(self, email: str, password: str):
            """Autentica y guarda el token."""
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers["Authorization"] = f"Bearer {self.token}"
            return response

        def get(self, endpoint: str, **kwargs):
            return self.session.get(f"{self.base_url}{endpoint}", **kwargs)

        def post(self, endpoint: str, json=None, data=None, **kwargs):
            return self.session.post(f"{self.base_url}{endpoint}", json=json, data=data, **kwargs)

        def put(self, endpoint: str, json=None, **kwargs):
            return self.session.put(f"{self.base_url}{endpoint}", json=json, **kwargs)

        def delete(self, endpoint: str, **kwargs):
            return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)

    return APIClient(api_base_url)


# ============================================================
# FIXTURES DE AUTENTICACION REMOTA
# ============================================================

@pytest.fixture(scope="session")
def admin_credentials():
    """Credenciales de administrador para tests de integracion."""
    return {
        "email": os.getenv("INTEGRATION_ADMIN_EMAIL", "admin@goalapp.com"),
        "password": os.getenv("INTEGRATION_ADMIN_PASSWORD", "admin123")
    }


@pytest.fixture(scope="session")
def admin_token(api_client, admin_credentials):
    """
    Token JWT de administrador para tests de integracion.
    Scope session: se obtiene una vez por sesion de tests.
    """
    response = api_client.login(
        admin_credentials["email"],
        admin_credentials["password"]
    )

    if response.status_code != 200:
        pytest.skip(f"No se pudo autenticar admin para integracion: {response.text}")

    return api_client.token


@pytest.fixture
def headers_auth_remote(admin_token):
    """Headers con autorizacion Bearer para API remota."""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================
# FIXTURES DE DATOS DE INTEGRACION
# ============================================================

@pytest.fixture
def datos_equipo_integracion():
    """Datos para crear equipo en tests de integracion."""
    import uuid
    return {
        "nombre": f"Equipo Integration Test {uuid.uuid4().hex[:8]}"
    }


@pytest.fixture
def datos_liga_integracion():
    """Datos para crear liga en tests de integracion."""
    import uuid
    return {
        "nombre": f"Liga Integration Test {uuid.uuid4().hex[:8]}",
        "temporada": "2025-2026"
    }


# ============================================================
# FIXTURES DE LIMPIEZA
# ============================================================

@pytest.fixture
def cleanup_created_entities(api_client):
    """
    Fixture que rastrea entidades creadas y las elimina al finalizar.
    Uso: entities_to_cleanup = cleanup_created_entities
    """
    created = []

    yield created

    # Limpiar entidades creadas en orden inverso (por dependencias)
    for entity_type, entity_id in reversed(created):
        try:
            api_client.delete(f"/{entity_type}/{entity_id}")
        except Exception:
            pass  # Ignorar errores de limpieza