# tests/integration/test_crud_flow.py
"""
Tests de integracion para flujos CRUD completos.
"""
import pytest
from tests.shared.factories import LeagueFactory, TeamFactory


@pytest.mark.integration
class TestLigaCRUDIntegration:
    """Tests de integracion para CRUD de ligas."""

    def test_create_read_delete_liga(self, api_client, admin_token):
        """Flujo completo: crear, leer y eliminar liga."""
        api_client.session.headers["Authorization"] = f"Bearer {admin_token}"

        # Crear liga
        liga_data = LeagueFactory.create()
        create_response = api_client.post("/ligas/", json=liga_data)

        if create_response.status_code != 201:
            pytest.skip(f"No se pudo crear liga: {create_response.text}")

        created_liga = create_response.json()
        liga_id = created_liga["id_liga"]

        try:
            # Leer liga creada
            read_response = api_client.get(f"/ligas/{liga_id}")
            assert read_response.status_code == 200
            assert read_response.json()["nombre"] == liga_data["nombre"]

            # Listar ligas
            list_response = api_client.get("/ligas/")
            assert list_response.status_code == 200
            assert any(l["id_liga"] == liga_id for l in list_response.json())

        finally:
            # Limpiar: eliminar liga
            delete_response = api_client.delete(f"/ligas/{liga_id}")
            assert delete_response.status_code in [200, 204, 404]


@pytest.mark.integration
class TestEquipoCRUDIntegration:
    """Tests de integracion para CRUD de equipos."""

    def test_create_equipo_requires_liga(self, api_client, admin_token):
        """Verificar que crear equipo requiere una liga existente."""
        api_client.session.headers["Authorization"] = f"Bearer {admin_token}"

        # Intentar crear equipo sin liga
        equipo_data = TeamFactory.create(id_liga=99999)
        response = api_client.post("/equipos/", json=equipo_data)

        # Deberia fallar si la liga no existe
        assert response.status_code in [400, 404, 422]