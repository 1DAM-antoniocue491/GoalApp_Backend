# tests/integration/test_auth_integration.py
"""
Tests de integracion para autenticacion contra la API remota.
"""
import pytest


@pytest.mark.integration
class TestAuthIntegration:
    """Tests de integracion para autenticacion."""

    def test_login_admin_success(self, api_client, admin_credentials):
        """Verificar que el admin puede hacer login en la API remota."""
        response = api_client.login(
            admin_credentials["email"],
            admin_credentials["password"]
        )
        assert response.status_code == 200, f"Login failed: {response.text}"

        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, api_client):
        """Verificar que login falla con credenciales invalidas."""
        response = api_client.login(
            "invalid@email.com",
            "wrongpassword"
        )
        assert response.status_code == 401

    def test_protected_endpoint_without_token(self, api_client):
        """Verificar que endpoints protegidos requieren autenticacion."""
        response = api_client.get("/usuarios/")
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self, api_client, admin_token):
        """Verificar que endpoints protegidos funcionan con token."""
        api_client.session.headers["Authorization"] = f"Bearer {admin_token}"
        response = api_client.get("/usuarios/me")
        assert response.status_code == 200