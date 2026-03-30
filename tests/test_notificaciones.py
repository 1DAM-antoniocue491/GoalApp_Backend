# tests/test_notificaciones.py
"""
Tests para el módulo de notificaciones.
"""


# ============================================================
# CREAR NOTIFICACIÓN
# ============================================================

class TestCrearNotificacion:
    """Tests para crear notificaciones."""

    def test_crear_notificacion_valida(self, client, headers_admin, usuario_ejemplo):
        """Crear notificación con datos válidos."""
        response = client.post(
            "/api/v1/notificaciones/",
            headers=headers_admin,
            json={
                "id_usuario": usuario_ejemplo.id_usuario,
                "mensaje": "Nueva notificación de prueba"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["mensaje"] == "Nueva notificación de prueba"
        assert data["leida"] == False

    def test_crear_notificacion_usuario_no_existente(self, client, headers_admin):
        """Crear notificación para usuario que no existe."""
        response = client.post(
            "/api/v1/notificaciones/",
            headers=headers_admin,
            json={
                "id_usuario": 999,
                "mensaje": "Notificación"
            }
        )

        assert response.status_code == 404


# ============================================================
# LISTAR NOTIFICACIONES
# ============================================================

class TestListarNotificaciones:
    """Tests para listar notificaciones."""

    def test_listar_notificaciones_usuario(self, client, headers_auth, notificacion_ejemplo):
        """Listar notificaciones de un usuario."""
        response = client.get(
            "/api/v1/notificaciones/",
            headers=headers_auth
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_listar_notificaciones_vacio(self, client, token_usuario):
        """Listar notificaciones cuando no hay ninguna."""
        response = client.get(
            "/api/v1/notificaciones/",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200
        assert response.json() == []


# ============================================================
# MARCAR COMO LEÍDA
# ============================================================

class TestMarcarNotificacionLeida:
    """Tests para marcar notificación como leída."""

    def test_marcar_notificacion_leida(self, client, headers_auth, notificacion_ejemplo):
        """Marcar notificación como leída."""
        response = client.patch(
            f"/api/v1/notificaciones/{notificacion_ejemplo.id_notificacion}/leer",
            headers=headers_auth
        )

        assert response.status_code == 200
        assert response.json()["leida"] == True

    def test_marcar_notificacion_no_existente(self, client, headers_auth):
        """Marcar notificación que no existe."""
        response = client.patch(
            "/api/v1/notificaciones/999/leer",
            headers=headers_auth
        )

        assert response.status_code == 404

    def test_marcar_notificacion_sin_autenticacion(self, client, notificacion_ejemplo):
        """Marcar notificación sin autenticación."""
        response = client.patch(
            f"/api/v1/notificaciones/{notificacion_ejemplo.id_notificacion}/leer"
        )

        assert response.status_code == 401


# ============================================================
# ELIMINAR NOTIFICACIÓN
# ============================================================

class TestEliminarNotificacion:
    """Tests para eliminar notificación."""

    def test_eliminar_notificacion_existente(self, client, headers_auth, notificacion_ejemplo):
        """Eliminar notificación que existe."""
        response = client.delete(
            f"/api/v1/notificaciones/{notificacion_ejemplo.id_notificacion}",
            headers=headers_auth
        )

        assert response.status_code == 204

    def test_eliminar_notificacion_no_existente(self, client, headers_auth):
        """Eliminar notificación que no existe."""
        response = client.delete(
            "/api/v1/notificaciones/999",
            headers=headers_auth
        )

        assert response.status_code == 404

    def test_eliminar_notificacion_sin_autenticacion(self, client, notificacion_ejemplo):
        """Eliminar notificación sin autenticación."""
        response = client.delete(
            f"/api/v1/notificaciones/{notificacion_ejemplo.id_notificacion}"
        )

        assert response.status_code == 401


# ============================================================
# NOTIFICACIONES NO LEÍDAS
# ============================================================

class TestNotificacionesNoLeidas:
    """Tests para obtener notificaciones no leídas."""

    def test_obtener_no_leidas(self, client, headers_auth, notificacion_ejemplo):
        """Obtener notificaciones no leídas."""
        response = client.get(
            "/api/v1/notificaciones/no-leidas",
            headers=headers_auth
        )

        assert response.status_code == 200
        data = response.json()
        # La notificación creada no está leída
        assert len(data) >= 1
        for notif in data:
            assert notif["leida"] == False

    def test_contar_no_leidas(self, client, headers_auth, notificacion_ejemplo):
        """Contar notificaciones no leídas."""
        response = client.get(
            "/api/v1/notificaciones/no-leidas/count",
            headers=headers_auth
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] >= 1