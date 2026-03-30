# tests/test_roles.py
"""
Tests para el módulo de roles.
"""


# ============================================================
# CREAR ROL
# ============================================================

class TestCrearRol:
    """Tests para crear roles."""

    def test_crear_rol_valido(self, client, headers_admin):
        """Crear rol con datos válidos."""
        response = client.post(
            "/api/v1/roles/",
            headers=headers_admin,
            json={
                "nombre": "nuevo_rol",
                "descripcion": "Descripción del rol"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "nuevo_rol"

    def test_crear_rol_duplicado(self, client, headers_admin, rol_admin):
        """Crear rol con nombre duplicado."""
        response = client.post(
            "/api/v1/roles/",
            headers=headers_admin,
            json={
                "nombre": "admin",
                "descripcion": "Otro admin"
            }
        )

        assert response.status_code == 400

    def test_crear_rol_sin_permisos(self, client, token_usuario):
        """Crear rol sin permisos de admin."""
        response = client.post(
            "/api/v1/roles/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "nombre": "nuevo_rol",
                "descripcion": "Descripción"
            }
        )

        assert response.status_code == 403


# ============================================================
# LISTAR ROLES
# ============================================================

class TestListarRoles:
    """Tests para listar roles."""

    def test_listar_roles_vacio(self, client, headers_admin):
        """Listar roles cuando no hay ninguno."""
        response = client.get(
            "/api/v1/roles/",
            headers=headers_admin
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_roles_con_datos(self, client, headers_admin, rol_admin, rol_coach):
        """Listar roles con datos."""
        response = client.get(
            "/api/v1/roles/",
            headers=headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


# ============================================================
# OBTENER ROL POR ID
# ============================================================

class TestObtenerRol:
    """Tests para obtener rol por ID."""

    def test_obtener_rol_existente(self, client, headers_admin, rol_admin):
        """Obtener rol que existe."""
        response = client.get(
            f"/api/v1/roles/{rol_admin.id_rol}",
            headers=headers_admin
        )

        assert response.status_code == 200
        assert response.json()["nombre"] == "admin"

    def test_obtener_rol_no_existente(self, client, headers_admin):
        """Obtener rol que no existe."""
        response = client.get(
            "/api/v1/roles/999",
            headers=headers_admin
        )

        assert response.status_code == 404


# ============================================================
# ACTUALIZAR ROL
# ============================================================

class TestActualizarRol:
    """Tests para actualizar rol."""

    def test_actualizar_nombre_rol(self, client, headers_admin, rol_admin):
        """Actualizar nombre de rol."""
        response = client.put(
            f"/api/v1/roles/{rol_admin.id_rol}",
            headers=headers_admin,
            json={"nombre": "administrador"}
        )

        assert response.status_code == 200
        assert response.json()["nombre"] == "administrador"

    def test_actualizar_descripcion_rol(self, client, headers_admin, rol_admin):
        """Actualizar descripción de rol."""
        response = client.put(
            f"/api/v1/roles/{rol_admin.id_rol}",
            headers=headers_admin,
            json={"descripcion": "Nueva descripción"}
        )

        assert response.status_code == 200
        assert response.json()["descripcion"] == "Nueva descripción"


# ============================================================
# ELIMINAR ROL
# ============================================================

class TestEliminarRol:
    """Tests para eliminar rol."""

    def test_eliminar_rol_existente(self, client, headers_admin, rol_coach):
        """Eliminar rol que existe."""
        response = client.delete(
            f"/api/v1/roles/{rol_coach.id_rol}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_rol_no_existente(self, client, headers_admin):
        """Eliminar rol que no existe."""
        response = client.delete(
            "/api/v1/roles/999",
            headers=headers_admin
        )

        assert response.status_code == 404


# ============================================================
# ASIGNAR ROL A USUARIO
# ============================================================

class TestAsignarRol:
    """Tests para asignar roles a usuarios."""

    def test_asignar_rol_usuario(self, client, headers_admin, usuario_ejemplo, rol_coach):
        """Asignar rol a usuario."""
        response = client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/roles/{rol_coach.id_rol}",
            headers=headers_admin
        )

        assert response.status_code == 200

    def test_asignar_rol_ya_tiene(self, client, headers_admin, usuario_admin, rol_admin):
        """Asignar rol que ya tiene."""
        response = client.post(
            f"/api/v1/usuarios/{usuario_admin.id_usuario}/roles/{rol_admin.id_rol}",
            headers=headers_admin
        )

        assert response.status_code == 400

    def test_asignar_rol_no_existente(self, client, headers_admin, usuario_ejemplo):
        """Asignar rol que no existe."""
        response = client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/roles/999",
            headers=headers_admin
        )

        assert response.status_code == 404

    def test_quitar_rol_usuario(self, client, headers_admin, usuario_admin, rol_admin):
        """Quitar rol a usuario."""
        response = client.delete(
            f"/api/v1/usuarios/{usuario_admin.id_usuario}/roles/{rol_admin.id_rol}",
            headers=headers_admin
        )

        assert response.status_code == 200