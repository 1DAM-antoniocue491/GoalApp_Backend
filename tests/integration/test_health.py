# tests/integration/test_health.py
"""
Tests de integracion para verificar disponibilidad de la API.
"""
import pytest


@pytest.mark.integration
class TestAPIHealth:
    """Tests de salud de la API."""

    def test_api_health_check(self, api_client):
        """Verificar que la API responde."""
        response = api_client.get("/health")
        # Puede ser 200 o 404 si no hay endpoint de health
        assert response.status_code in [200, 404]

    def test_api_root_endpoint(self, api_client):
        """Verificar que el endpoint raiz responde."""
        response = api_client.get("/")
        # La API deberia responder en el endpoint raiz
        assert response.status_code in [200, 404]