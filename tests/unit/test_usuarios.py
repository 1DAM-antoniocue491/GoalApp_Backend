# tests/test_usuarios.py
"""
Tests para el módulo de usuarios.
"""
import pytest
from app.models.usuario_rol import UsuarioRol


# ============================================================
# LISTAR USUARIOS
# ============================================================

class TestListarUsuarios:
    """Tests para listar usuarios."""

    def test_listar_usuarios_vacio(self, client):
        """Listar usuarios cuando no hay ninguno."""
        response = client.get("/api/v1/usuarios/")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_usuarios_con_datos(self, client, usuario_ejemplo):
        """Listar usuarios con datos."""
        response = client.get("/api/v1/usuarios/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == usuario_ejemplo.email

    def test_listar_usuarios_paginacion(self, client):
        """Listar usuarios con paginación."""
        # Crear varios usuarios
        for i in range(15):
            client.post(
                "/api/v1/usuarios/",
                json={
                    "nombre": f"Usuario {i}",
                    "email": f"usuario{i}@email.com",
                    "password": "password123"
                }
            )

        # Obtener primera página
        response = client.get("/api/v1/usuarios/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Obtener segunda página
        response = client.get("/api/v1/usuarios/?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


# ============================================================
# OBTENER USUARIO POR ID
# ============================================================

class TestObtenerUsuario:
    """Tests para obtener usuario por ID."""

    def test_obtener_usuario_existente(self, client, usuario_ejemplo):
        """Obtener usuario que existe."""
        response = client.get(f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}")

        assert response.status_code == 200
        data = response.json()
        assert data["id_usuario"] == usuario_ejemplo.id_usuario
        assert data["nombre"] == usuario_ejemplo.nombre
        assert data["email"] == usuario_ejemplo.email

    def test_obtener_usuario_no_existente(self, client):
        """Obtener usuario que no existe."""
        response = client.get("/api/v1/usuarios/999")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"].lower()


# ============================================================
# ACTUALIZAR USUARIO
# ============================================================

class TestActualizarUsuario:
    """Tests para actualizar usuario."""

    def test_actualizar_nombre(self, client, usuario_ejemplo, token_usuario):
        """Actualizar nombre de usuario."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"nombre": "Nombre Actualizado"}
        )

        assert response.status_code == 200
        assert response.json()["nombre"] == "Nombre Actualizado"

    def test_actualizar_email(self, client, usuario_ejemplo, token_usuario):
        """Actualizar email de usuario."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"email": "nuevo@email.com"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "nuevo@email.com"

    def test_actualizar_email_duplicado(self, client, usuario_ejemplo, usuario2_ejemplo, token_usuario):
        """Actualizar email a uno ya existente."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"email": usuario2_ejemplo.email}
        )

        assert response.status_code == 400

    def test_actualizar_telefono_valido(self, client, usuario_ejemplo, token_usuario):
        """Actualizar teléfono con formato válido."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"telefono": "+34612345678"}
        )

        assert response.status_code == 200
        assert response.json()["telefono"] == "+34612345678"

    def test_actualizar_telefono_invalido(self, client, usuario_ejemplo, token_usuario):
        """Actualizar teléfono con formato inválido."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"telefono": "123"}  # Muy corto
        )

        assert response.status_code == 422

    def test_actualizar_usuario_no_existente(self, client, token_usuario):
        """Actualizar usuario que no existe."""
        response = client.put(
            "/api/v1/usuarios/999",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"nombre": "Nombre"}
        )

        assert response.status_code == 404

    def test_actualizar_genero(self, client, usuario_ejemplo, token_usuario):
        """Actualizar género de usuario."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"genero": "masculino"}
        )

        assert response.status_code == 200
        assert response.json()["genero"] == "masculino"

    def test_actualizar_fecha_nacimiento(self, client, usuario_ejemplo, token_usuario):
        """Actualizar fecha de nacimiento."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"fecha_nacimiento": "1990-01-15"}
        )

        assert response.status_code == 200
        assert response.json()["fecha_nacimiento"] == "1990-01-15"


# ============================================================
# ELIMINAR USUARIO
# ============================================================

class TestEliminarUsuario:
    """Tests para eliminar usuario."""

    def test_eliminar_usuario_existente(self, client, usuario_ejemplo, token_usuario):
        """Eliminar usuario que existe."""
        response = client.delete(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 204

        # Verificar que ya no existe
        response = client.get(f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}")
        assert response.status_code == 404

    def test_eliminar_usuario_no_existente(self, client, token_usuario):
        """Eliminar usuario que no existe."""
        response = client.delete(
            "/api/v1/usuarios/999",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 404


# ============================================================
# SEGUIR LIGAS
# ============================================================

class TestSeguirLigas:
    """Tests para seguir/dejar de seguir ligas."""

    def test_seguir_liga(self, client, usuario_ejemplo, token_usuario, liga_ejemplo):
        """Seguir una liga."""
        response = client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200

    def test_seguir_liga_ya_seguida(self, client, usuario_ejemplo, token_usuario, liga_ejemplo):
        """Intentar seguir una liga ya seguida."""
        # Seguir primero
        client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        # Intentar seguir de nuevo
        response = client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 400

    def test_dejar_seguir_liga(self, client, usuario_ejemplo, token_usuario, liga_ejemplo):
        """Dejar de seguir una liga."""
        # Seguir primero
        client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        # Dejar de seguir
        response = client.delete(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200

    def test_dejar_seguir_liga_no_seguida(self, client, usuario_ejemplo, token_usuario, liga_ejemplo):
        """Dejar de seguir una liga que no se sigue."""
        response = client.delete(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 400

    def test_listar_ligas_seguidas(self, client, usuario_ejemplo, token_usuario, liga_ejemplo):
        """Listar ligas seguidas por un usuario."""
        # Seguir liga
        client.post(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/seguir/{liga_ejemplo.id_liga}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        response = client.get(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}/ligas",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id_liga"] == liga_ejemplo.id_liga


# ============================================================
# LIGAS CON ROL ASIGNADO
# ============================================================

class TestLigasConRol:
    """Tests para obtener las ligas donde el usuario tiene un rol."""

    def test_obtener_ligas_con_rol_sin_roles(self, client, token_usuario):
        """Obtener ligas con rol cuando el usuario no tiene roles asignados."""
        response = client.get(
            "/api/v1/usuarios/me/ligas",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_obtener_ligas_con_rol_admin(self, client, usuario_admin, token_admin):
        """Obtener ligas donde el usuario tiene rol admin."""
        response = client.get(
            "/api/v1/usuarios/me/ligas",
            headers={"Authorization": f"Bearer {token_admin}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rol"] == "admin"

    def test_obtener_ligas_con_rol_multiples_ligas(
        self, client, usuario_ejemplo, liga_ejemplo, liga2_ejemplo, rol_admin, rol_coach, db, token_usuario
    ):
        """Obtener ligas donde el usuario tiene diferentes roles."""
        # Asignar rol admin en liga 1
        usuario_rol1 = UsuarioRol(
            id_usuario=usuario_ejemplo.id_usuario,
            id_rol=rol_admin.id_rol,
            id_liga=liga_ejemplo.id_liga
        )
        db.add(usuario_rol1)

        # Asignar rol coach en liga 2
        usuario_rol2 = UsuarioRol(
            id_usuario=usuario_ejemplo.id_usuario,
            id_rol=rol_coach.id_rol,
            id_liga=liga2_ejemplo.id_liga
        )
        db.add(usuario_rol2)
        db.commit()

        response = client.get(
            "/api/v1/usuarios/me/ligas",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verificar que estan ambas ligas con sus roles correctos
        ligas_dict = {item["id_liga"]: item["rol"] for item in data}
        assert ligas_dict[liga_ejemplo.id_liga] == "admin"
        assert ligas_dict[liga2_ejemplo.id_liga] == "coach"

    def test_obtener_ligas_sin_autenticacion(self, client):
        """Intentar obtener ligas sin autenticacion debe fallar."""
        response = client.get("/api/v1/usuarios/me/ligas")

        assert response.status_code == 401