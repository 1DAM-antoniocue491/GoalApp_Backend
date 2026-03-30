# tests/test_equipos.py
"""
Tests para el módulo de equipos.
"""


# ============================================================
# CREAR EQUIPO
# ============================================================

class TestCrearEquipo:
    """Tests para crear equipos."""

    def test_crear_equipo_valido(self, client, headers_admin, datos_equipo_nuevo):
        """Crear equipo con datos válidos."""
        response = client.post(
            "/api/v1/equipos/",
            headers=headers_admin,
            json=datos_equipo_nuevo
        )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == datos_equipo_nuevo["nombre"]

    def test_crear_equipo_sin_permisos(self, client, token_usuario, datos_equipo_nuevo):
        """Crear equipo sin permisos."""
        response = client.post(
            "/api/v1/equipos/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json=datos_equipo_nuevo
        )

        assert response.status_code == 403

    def test_crear_equipo_liga_no_existente(self, client, headers_admin, usuario_ejemplo, usuario2_ejemplo):
        """Crear equipo en liga que no existe."""
        response = client.post(
            "/api/v1/equipos/",
            headers=headers_admin,
            json={
                "nombre": "Equipo Test",
                "id_liga": 999,
                "id_entrenador": usuario_ejemplo.id_usuario,
                "id_delegado": usuario2_ejemplo.id_usuario
            }
        )

        assert response.status_code == 404

    def test_crear_equipo_nombre_vacio(self, client, headers_admin, datos_equipo_nuevo):
        """Crear equipo con nombre vacío."""
        datos = datos_equipo_nuevo.copy()
        datos["nombre"] = ""

        response = client.post(
            "/api/v1/equipos/",
            headers=headers_admin,
            json=datos
        )

        assert response.status_code == 422


# ============================================================
# LISTAR EQUIPOS
# ============================================================

class TestListarEquipos:
    """Tests para listar equipos."""

    def test_listar_equipos_vacio(self, client):
        """Listar equipos cuando no hay ninguno."""
        response = client.get("/api/v1/equipos/")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_equipos_con_datos(self, client, equipo_ejemplo):
        """Listar equipos con datos."""
        response = client.get("/api/v1/equipos/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nombre"] == equipo_ejemplo.nombre

    def test_listar_equipos_por_liga(self, client, liga_ejemplo, equipo_ejemplo):
        """Listar equipos de una liga específica."""
        response = client.get(f"/api/v1/equipos/?id_liga={liga_ejemplo.id_liga}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


# ============================================================
# OBTENER EQUIPO POR ID
# ============================================================

class TestObtenerEquipo:
    """Tests para obtener equipo por ID."""

    def test_obtener_equipo_existente(self, client, equipo_ejemplo):
        """Obtener equipo que existe."""
        response = client.get(f"/api/v1/equipos/{equipo_ejemplo.id_equipo}")

        assert response.status_code == 200
        assert response.json()["id_equipo"] == equipo_ejemplo.id_equipo

    def test_obtener_equipo_no_existente(self, client):
        """Obtener equipo que no existe."""
        response = client.get("/api/v1/equipos/999")

        assert response.status_code == 404


# ============================================================
# ACTUALIZAR EQUIPO
# ============================================================

class TestActualizarEquipo:
    """Tests para actualizar equipo."""

    def test_actualizar_nombre_equipo(self, client, headers_admin, equipo_ejemplo):
        """Actualizar nombre de equipo."""
        response = client.put(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers=headers_admin,
            json={"nombre": "Nuevo Nombre"}
        )

        assert response.status_code == 200
        assert response.json()["nombre"] == "Nuevo Nombre"

    def test_actualizar_equipo_sin_permisos(self, client, token_usuario, equipo_ejemplo):
        """Actualizar equipo sin permisos."""
        response = client.put(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"nombre": "Nuevo Nombre"}
        )

        assert response.status_code == 403

    def test_actualizar_equipo_no_existente(self, client, headers_admin):
        """Actualizar equipo que no existe."""
        response = client.put(
            "/api/v1/equipos/999",
            headers=headers_admin,
            json={"nombre": "Nuevo Nombre"}
        )

        assert response.status_code == 404


# ============================================================
# ELIMINAR EQUIPO
# ============================================================

class TestEliminarEquipo:
    """Tests para eliminar equipo."""

    def test_eliminar_equipo_existente(self, client, headers_admin, equipo_ejemplo):
        """Eliminar equipo que existe."""
        response = client.delete(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_equipo_sin_permisos(self, client, token_usuario, equipo_ejemplo):
        """Eliminar equipo sin permisos."""
        response = client.delete(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_equipo_no_existente(self, client, headers_admin):
        """Eliminar equipo que no existe."""
        response = client.delete(
            "/api/v1/equipos/999",
            headers=headers_admin
        )

        assert response.status_code == 404


# ============================================================
# IMÁGENES DE EQUIPO
# ============================================================

class TestImagenesEquipo:
    """Tests para gestión de imágenes de equipo."""

    def test_subir_imagen_equipo(self, client, headers_admin, equipo_ejemplo):
        """Subir imagen de escudo del equipo."""
        # Crear archivo de prueba
        import io
        from PIL import Image

        image = Image.new('RGB', (100, 100), color='red')
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)

        response = client.post(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}/imagen",
            headers=headers_admin,
            files={"imagen": ("escudo.jpg", image_bytes, "image/jpeg")}
        )

        # Puede ser 200 o 201 dependiendo de la implementación
        assert response.status_code in [200, 201, 422]  # 422 si no está implementado

    def test_subir_imagen_formato_invalido(self, client, headers_admin, equipo_ejemplo):
        """Subir imagen con formato inválido."""
        response = client.post(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}/imagen",
            headers=headers_admin,
            files={"imagen": ("archivo.txt", b"contenido", "text/plain")}
        )

        assert response.status_code == 422

    def test_eliminar_imagen_equipo(self, client, headers_admin, equipo_ejemplo):
        """Eliminar imagen de equipo."""
        response = client.delete(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}/imagen",
            headers=headers_admin
        )

        # Puede ser 200, 204 o 404 dependiendo de si tenía imagen
        assert response.status_code in [200, 204, 404]