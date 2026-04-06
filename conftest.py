# conftest.py (raiz del proyecto)
"""
Configuracion global de pytest para todo el proyecto.
Define fixtures base y configuracion comun.
"""
import pytest
import os

# Asegurar que estamos en modo test
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"


def pytest_addoption(parser):
    """Anade opciones personalizadas a pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Ejecutar tests de integracion (requiere API remota)"
    )
    parser.addoption(
        "--api-url",
        action="store",
        default=None,
        help="URL base de la API para tests de integracion"
    )


def pytest_configure(config):
    """Configuracion inicial de pytest."""
    # Registrar marcadores personalizados
    config.addinivalue_line("markers", "unit: Tests unitarios aislados")
    config.addinivalue_line("markers", "integration: Tests de integracion con API remota")
    config.addinivalue_line("markers", "slow: Tests que tardan mas tiempo")
    config.addinivalue_line("markers", "smoke: Tests de verificacion rapida")


def pytest_collection_modifyitems(config, items):
    """Modifica la coleccion de tests segun opciones."""
    # Si no se especifica --integration, excluir tests marcados como integration
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(
            reason="Usar --integration para ejecutar tests de integracion"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)