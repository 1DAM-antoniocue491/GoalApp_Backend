# tests/test_partidos.py
"""
Tests para el módulo de partidos.
"""
from datetime import datetime, timedelta, timezone


# ============================================================
# CREAR PARTIDO
# ============================================================

class TestCrearPartido:
    """Tests para crear partidos."""

    def test_crear_partido_valido(self, client, headers_admin, liga_ejemplo, equipo_ejemplo, equipo2_ejemplo):
        """Crear partido con datos válidos."""
        response = client.post(
            "/api/v1/partidos/",
            headers=headers_admin,
            json={
                "id_liga": liga_ejemplo.id_liga,
                "id_equipo_local": equipo_ejemplo.id_equipo,
                "id_equipo_visitante": equipo2_ejemplo.id_equipo,
                "fecha": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "estado": "programado"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "programado"

    def test_crear_partido_sin_permisos(self, client, token_usuario, liga_ejemplo, equipo_ejemplo, equipo2_ejemplo):
        """Crear partido sin permisos."""
        response = client.post(
            "/api/v1/partidos/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "id_liga": liga_ejemplo.id_liga,
                "id_equipo_local": equipo_ejemplo.id_equipo,
                "id_equipo_visitante": equipo2_ejemplo.id_equipo,
                "fecha": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "estado": "programado"
            }
        )

        assert response.status_code == 403

    def test_crear_partido_mismo_equipo(self, client, headers_admin, liga_ejemplo, equipo_ejemplo):
        """Crear partido con el mismo equipo como local y visitante."""
        response = client.post(
            "/api/v1/partidos/",
            headers=headers_admin,
            json={
                "id_liga": liga_ejemplo.id_liga,
                "id_equipo_local": equipo_ejemplo.id_equipo,
                "id_equipo_visitante": equipo_ejemplo.id_equipo,
                "fecha": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "estado": "programado"
            }
        )

        # Puede ser 400 o 422 dependiendo de la validación
        assert response.status_code in [400, 422]

    def test_crear_partido_liga_no_existente(self, client, headers_admin, equipo_ejemplo, equipo2_ejemplo):
        """Crear partido en liga que no existe."""
        response = client.post(
            "/api/v1/partidos/",
            headers=headers_admin,
            json={
                "id_liga": 999,
                "id_equipo_local": equipo_ejemplo.id_equipo,
                "id_equipo_visitante": equipo2_ejemplo.id_equipo,
                "fecha": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "estado": "programado"
            }
        )

        assert response.status_code == 404


# ============================================================
# LISTAR PARTIDOS
# ============================================================

class TestListarPartidos:
    """Tests para listar partidos."""

    def test_listar_partidos_vacio(self, client):
        """Listar partidos cuando no hay ninguno."""
        response = client.get("/api/v1/partidos/")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_partidos_con_datos(self, client, partido_ejemplo):
        """Listar partidos con datos."""
        response = client.get("/api/v1/partidos/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_listar_partidos_por_liga(self, client, liga_ejemplo, partido_ejemplo):
        """Listar partidos de una liga específica."""
        response = client.get(f"/api/v1/partidos/?id_liga={liga_ejemplo.id_liga}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


# ============================================================
# OBTENER PARTIDO POR ID
# ============================================================

class TestObtenerPartido:
    """Tests para obtener partido por ID."""

    def test_obtener_partido_existente(self, client, partido_ejemplo):
        """Obtener partido que existe."""
        response = client.get(f"/api/v1/partidos/{partido_ejemplo.id_partido}")

        assert response.status_code == 200
        assert response.json()["id_partido"] == partido_ejemplo.id_partido

    def test_obtener_partido_no_existente(self, client):
        """Obtener partido que no existe."""
        response = client.get("/api/v1/partidos/999")

        assert response.status_code == 404


# ============================================================
# ACTUALIZAR PARTIDO
# ============================================================

class TestActualizarPartido:
    """Tests para actualizar partido."""

    def test_actualizar_resultado(self, client, headers_admin, partido_ejemplo):
        """Actualizar resultado de partido."""
        response = client.put(
            f"/api/v1/partidos/{partido_ejemplo.id_partido}",
            headers=headers_admin,
            json={
                "goles_local": 2,
                "goles_visitante": 1
            }
        )

        assert response.status_code == 200
        assert response.json()["goles_local"] == 2
        assert response.json()["goles_visitante"] == 1

    def test_actualizar_estado_partido(self, client, headers_admin, partido_ejemplo):
        """Actualizar estado de partido."""
        response = client.put(
            f"/api/v1/partidos/{partido_ejemplo.id_partido}",
            headers=headers_admin,
            json={"estado": "en_juego"}
        )

        assert response.status_code == 200
        assert response.json()["estado"] == "en_juego"

    def test_actualizar_partido_sin_permisos(self, client, token_usuario, partido_ejemplo):
        """Actualizar partido sin permisos."""
        response = client.put(
            f"/api/v1/partidos/{partido_ejemplo.id_partido}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"estado": "finalizado"}
        )

        assert response.status_code == 403


# ============================================================
# ELIMINAR PARTIDO
# ============================================================

class TestEliminarPartido:
    """Tests para eliminar partido."""

    def test_eliminar_partido_existente(self, client, headers_admin, partido_ejemplo):
        """Eliminar partido que existe."""
        response = client.delete(
            f"/api/v1/partidos/{partido_ejemplo.id_partido}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_partido_sin_permisos(self, client, token_usuario, partido_ejemplo):
        """Eliminar partido sin permisos."""
        response = client.delete(
            f"/api/v1/partidos/{partido_ejemplo.id_partido}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_partido_no_existente(self, client, headers_admin):
        """Eliminar partido que no existe."""
        response = client.delete(
            "/api/v1/partidos/999",
            headers=headers_admin
        )

        assert response.status_code == 404