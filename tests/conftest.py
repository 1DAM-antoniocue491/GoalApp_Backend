# tests/conftest.py
"""
Fixtures base compartidas entre tests unitarios e integracion.
Solo incluye fixtures que NO dependen del tipo de BD.
"""
import pytest


# ============================================================
# FIXTURES DE DATOS (no dependen de BD)
# ============================================================

@pytest.fixture
def datos_usuario_nuevo():
    """Datos para crear un nuevo usuario."""
    return {
        "nombre": "Nuevo Usuario",
        "email": "nuevo@email.com",
        "password": "password123"
    }


@pytest.fixture
def datos_liga_nueva():
    """Datos para crear una nueva liga."""
    return {
        "nombre": "Nueva Liga",
        "temporada": "2024-2025"
    }


@pytest.fixture
def datos_equipo_nuevo():
    """Datos base para crear un nuevo equipo (sin IDs)."""
    return {
        "nombre": "Nuevo Equipo"
    }


# ============================================================
# FIXTURES DE CONFIGURACION
# ============================================================

@pytest.fixture
def api_base_url(request):
    """URL base de la API para tests de integracion."""
    # Prioridad: opcion de linea de comandos > variable de entorno > default
    url = request.config.getoption("--api-url")
    if url:
        return url

    import os
    url = os.getenv("INTEGRATION_API_URL", "http://localhost:8000/api/v1")
    return url