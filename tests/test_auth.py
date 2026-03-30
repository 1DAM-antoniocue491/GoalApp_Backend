# tests/test_auth.py
"""
Tests para el módulo de autenticación.
"""
import pytest
from datetime import datetime, timedelta


# ============================================================
# LOGIN
# ============================================================

class TestLogin:
    """Tests para el endpoint de login."""

    def test_login_correcto(self, client, usuario_ejemplo):
        """Login con credenciales correctas."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": usuario_ejemplo.email,
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_password_incorrecta(self, client, usuario_ejemplo):
        """Login con contraseña incorrecta."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": usuario_ejemplo.email,
                "password": "contraseña_incorrecta"
            }
        )

        assert response.status_code == 401
        assert "Credenciales incorrectas" in response.json()["detail"]

    def test_login_usuario_no_existente(self, client):
        """Login con usuario que no existe."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "noexiste@email.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "Credenciales incorrectas" in response.json()["detail"]

    def test_login_email_invalido(self, client):
        """Login con formato de email inválido."""
        # OAuth2PasswordRequestForm acepta cualquier string como username
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "no-es-email",
                "password": "password123"
            }
        )

        # El login falla porque no encuentra el usuario
        assert response.status_code == 401

    def test_login_campos_vacios(self, client):
        """Login con campos vacíos."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "",
                "password": ""
            }
        )

        assert response.status_code == 422  # Validation error


# ============================================================
# OBTENER PERFIL
# ============================================================

class TestObtenerPerfil:
    """Tests para el endpoint /auth/me."""

    def test_obtener_perfil_con_token(self, client, token_usuario):
        """Obtener perfil con token válido."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "id_usuario" in data
        assert "nombre" in data
        assert "email" in data
        assert "password" not in data  # No debe incluir contraseña

    def test_obtener_perfil_sin_token(self, client):
        """Obtener perfil sin token debe fallar."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Token inválido" in response.json()["detail"]

    def test_obtener_perfil_token_invalido(self, client):
        """Obtener perfil con token inválido."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token_invalido"}
        )

        assert response.status_code == 401

    def test_obtener_perfil_token_malformado(self, client):
        """Obtener perfil con token mal formado."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "token_sin_bearer"}
        )

        assert response.status_code == 401


# ============================================================
# REFRESH TOKEN
# ============================================================

class TestRefreshToken:
    """Tests para el endpoint de refresh token."""

    def test_refresh_token_valido(self, client, token_usuario):
        """Refrescar token válido."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"token": token_usuario}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # El nuevo token debe ser diferente
        assert data["access_token"] != token_usuario

    def test_refresh_token_invalido(self, client):
        """Refrescar con token inválido."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"token": "token_invalido"}
        )

        assert response.status_code == 401
        assert "Token inválido" in response.json()["detail"]


# ============================================================
# RECUPERACIÓN DE CONTRASEÑA
# ============================================================

class TestRecuperacionPassword:
    """Tests para recuperación de contraseña."""

    def test_forgot_password_usuario_existente(self, client, usuario_ejemplo):
        """Solicitar recuperación con email existente."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": usuario_ejemplo.email}
        )

        assert response.status_code == 200
        assert "mensaje" in response.json()

    def test_forgot_password_usuario_no_existente(self, client):
        """Solicitar recuperación con email no existente."""
        # Por seguridad, siempre devuelve éxito
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "noexiste@email.com"}
        )

        assert response.status_code == 200
        assert "mensaje" in response.json()

    def test_forgot_password_email_vacio(self, client):
        """Solicitar recuperación con email vacío."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": ""}
        )

        assert response.status_code == 422  # Validation error


# ============================================================
# REGISTRO DE USUARIO
# ============================================================

class TestRegistroUsuario:
    """Tests para registro de usuario."""

    def test_registro_usuario_valido(self, client, datos_usuario_nuevo):
        """Registrar usuario con datos válidos."""
        response = client.post(
            "/api/v1/usuarios/",
            json=datos_usuario_nuevo
        )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == datos_usuario_nuevo["nombre"]
        assert data["email"] == datos_usuario_nuevo["email"]
        assert "password" not in data

    def test_registro_email_duplicado(self, client, usuario_ejemplo):
        """Registrar usuario con email ya existente."""
        response = client.post(
            "/api/v1/usuarios/",
            json={
                "nombre": "Otro Usuario",
                "email": usuario_ejemplo.email,
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "email ya está registrado" in response.json()["detail"].lower()

    def test_registro_password_corta(self, client):
        """Registrar con contraseña muy corta."""
        response = client.post(
            "/api/v1/usuarios/",
            json={
                "nombre": "Usuario Test",
                "email": "test@email.com",
                "password": "123"  # Muy corta
            }
        )

        assert response.status_code == 422

    def test_registro_email_invalido(self, client):
        """Registrar con email inválido."""
        response = client.post(
            "/api/v1/usuarios/",
            json={
                "nombre": "Usuario Test",
                "email": "no-es-email",
                "password": "password123"
            }
        )

        assert response.status_code == 422

    def test_registro_nombre_vacio(self, client):
        """Registrar con nombre vacío."""
        response = client.post(
            "/api/v1/usuarios/",
            json={
                "nombre": "",
                "email": "test@email.com",
                "password": "password123"
            }
        )

        assert response.status_code == 422


# ============================================================
# CAMBIAR CONTRASEÑA
# ============================================================

class TestCambiarPassword:
    """Tests para cambio de contraseña."""

    def test_cambiar_password_usuario_existente(self, client, usuario_ejemplo, token_usuario):
        """Cambiar contraseña de usuario existente."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"contraseña": "nueva_password123"}
        )

        assert response.status_code == 200

        # Verificar que la nueva contraseña funciona
        response_login = client.post(
            "/api/v1/auth/login",
            data={
                "username": usuario_ejemplo.email,
                "password": "nueva_password123"
            }
        )

        assert response_login.status_code == 200