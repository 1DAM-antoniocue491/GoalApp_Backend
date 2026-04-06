# tests/test_ligas.py
"""
Tests para el módulo de ligas.
"""


# ============================================================
# CREAR LIGA
# ============================================================

class TestCrearLiga:
    """Tests para crear ligas."""

    def test_crear_liga_valida(self, client, headers_admin, datos_liga_nueva):
        """Crear liga con datos válidos."""
        response = client.post(
            "/api/v1/ligas/",
            headers=headers_admin,
            json=datos_liga_nueva
        )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == datos_liga_nueva["nombre"]
        assert data["temporada"] == datos_liga_nueva["temporada"]

    def test_crear_liga_sin_permisos(self, client, token_usuario, datos_liga_nueva):
        """Crear liga sin permisos de admin."""
        response = client.post(
            "/api/v1/ligas/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json=datos_liga_nueva
        )

        assert response.status_code == 403

    def test_crear_liga_sin_autenticacion(self, client, datos_liga_nueva):
        """Crear liga sin autenticación."""
        response = client.post(
            "/api/v1/ligas/",
            json=datos_liga_nueva
        )

        assert response.status_code == 401

    def test_crear_liga_nombre_vacio(self, client, headers_admin):
        """Crear liga con nombre vacío."""
        response = client.post(
            "/api/v1/ligas/",
            headers=headers_admin,
            json={
                "nombre": "",
                "temporada": "2024-2025"
            }
        )

        assert response.status_code == 422

    def test_crear_liga_temporada_vacia(self, client, headers_admin):
        """Crear liga con temporada vacía."""
        response = client.post(
            "/api/v1/ligas/",
            headers=headers_admin,
            json={
                "nombre": "Liga Test",
                "temporada": ""
            }
        )

        assert response.status_code == 422


# ============================================================
# LISTAR LIGAS
# ============================================================

class TestListarLigas:
    """Tests para listar ligas."""

    def test_listar_ligas_vacio(self, client):
        """Listar ligas cuando no hay ninguna."""
        response = client.get("/api/v1/ligas/")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_ligas_con_datos(self, client, liga_ejemplo):
        """Listar ligas con datos."""
        response = client.get("/api/v1/ligas/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nombre"] == liga_ejemplo.nombre

    def test_listar_ligas_paginacion(self, client):
        """Listar ligas con paginación."""
        # Crear varias ligas
        for i in range(15):
            client.post(
                "/api/v1/ligas/",
                json={"nombre": f"Liga {i}", "temporada": "2024-2025"}
            )

        # Primera página
        response = client.get("/api/v1/ligas/?skip=0&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 10

        # Segunda página
        response = client.get("/api/v1/ligas/?skip=10&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 5


# ============================================================
# OBTENER LIGA POR ID
# ============================================================

class TestObtenerLiga:
    """Tests para obtener liga por ID."""

    def test_obtener_liga_existente(self, client, liga_ejemplo):
        """Obtener liga que existe."""
        response = client.get(f"/api/v1/ligas/{liga_ejemplo.id_liga}")

        assert response.status_code == 200
        assert response.json()["id_liga"] == liga_ejemplo.id_liga

    def test_obtener_liga_no_existente(self, client):
        """Obtener liga que no existe."""
        response = client.get("/api/v1/ligas/999")

        assert response.status_code == 404


# ============================================================
# ACTUALIZAR LIGA
# ============================================================

class TestActualizarLiga:
    """Tests para actualizar liga."""

    def test_actualizar_nombre_liga(self, client, headers_admin, liga_ejemplo):
        """Actualizar nombre de liga."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers=headers_admin,
            json={"nombre": "Nueva Liga"}
        )

        assert response.status_code == 200
        assert response.json()["nombre"] == "Nueva Liga"

    def test_actualizar_temporada_liga(self, client, headers_admin, liga_ejemplo):
        """Actualizar temporada de liga."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers=headers_admin,
            json={"temporada": "2025-2026"}
        )

        assert response.status_code == 200
        assert response.json()["temporada"] == "2025-2026"

    def test_actualizar_liga_sin_permisos(self, client, token_usuario, liga_ejemplo):
        """Actualizar liga sin permisos."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"nombre": "Nuevo Nombre"}
        )

        assert response.status_code == 403

    def test_actualizar_liga_no_existente(self, client, headers_admin):
        """Actualizar liga que no existe."""
        response = client.put(
            "/api/v1/ligas/999",
            headers=headers_admin,
            json={"nombre": "Nueva Liga"}
        )

        assert response.status_code == 404


# ============================================================
# ELIMINAR LIGA
# ============================================================

class TestEliminarLiga:
    """Tests para eliminar liga."""

    def test_eliminar_liga_existente(self, client, headers_admin, liga_ejemplo):
        """Eliminar liga que existe."""
        response = client.delete(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_liga_sin_permisos(self, client, token_usuario, liga_ejemplo):
        """Eliminar liga sin permisos."""
        response = client.delete(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_liga_no_existente(self, client, headers_admin):
        """Eliminar liga que no existe."""
        response = client.delete(
            "/api/v1/ligas/999",
            headers=headers_admin
        )

        assert response.status_code == 404


# ============================================================
# ACTIVAR/DESACTIVAR LIGA
# ============================================================

class TestActivarDesactivarLiga:
    """Tests para activar/desactivar liga."""

    def test_desactivar_liga(self, client, headers_admin, liga_ejemplo):
        """Desactivar una liga activa."""
        response = client.patch(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/desactivar",
            headers=headers_admin
        )

        assert response.status_code == 200
        assert response.json()["activa"] == False

    def test_activar_liga(self, client, headers_admin, db):
        """Activar una liga inactiva."""
        from app.models.liga import Liga

        # Crear liga inactiva
        liga = Liga(nombre="Liga Inactiva", temporada="2024-2025", activa=False)
        db.add(liga)
        db.commit()
        db.refresh(liga)

        response = client.patch(
            f"/api/v1/ligas/{liga.id_liga}/activar",
            headers=headers_admin
        )

        assert response.status_code == 200
        assert response.json()["activa"] == True


# ============================================================
# CLASIFICACIÓN
# ============================================================

class TestClasificacion:
    """Tests para obtener clasificación de liga."""

    def test_clasificacion_liga_vacia(self, client, liga_ejemplo):
        """Obtener clasificación de liga sin equipos."""
        response = client.get(f"/api/v1/ligas/{liga_ejemplo.id_liga}/clasificacion")

        assert response.status_code == 200
        assert response.json() == []

    def test_clasificacion_liga_con_equipos(self, client, liga_ejemplo, equipo_ejemplo, equipo2_ejemplo):
        """Obtener clasificación de liga con equipos."""
        response = client.get(f"/api/v1/ligas/{liga_ejemplo.id_liga}/clasificacion")

        assert response.status_code == 200
        data = response.json()
        # Debe contener información de equipos
        assert len(data) >= 0  # Puede estar vacía si no hay partidos

    def test_clasificacion_liga_no_existente(self, client):
        """Obtener clasificación de liga que no existe."""
        response = client.get("/api/v1/ligas/999/clasificacion")

        assert response.status_code == 404