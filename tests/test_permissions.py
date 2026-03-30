# tests/test_permissions.py
"""
Tests para verificación de permisos por rol.
"""


# ============================================================
# PERMISOS DE ADMIN
# ============================================================

class TestPermisosAdmin:
    """Tests para permisos de administrador."""

    def test_admin_puede_crear_ligas(self, client, headers_admin, datos_liga_nueva):
        """Admin puede crear ligas."""
        response = client.post(
            "/api/v1/ligas/",
            headers=headers_admin,
            json=datos_liga_nueva
        )

        assert response.status_code == 201

    def test_admin_puede_crear_equipos(self, client, headers_admin, datos_equipo_nuevo):
        """Admin puede crear equipos."""
        response = client.post(
            "/api/v1/equipos/",
            headers=headers_admin,
            json=datos_equipo_nuevo
        )

        assert response.status_code == 201

    def test_admin_puede_crear_roles(self, client, headers_admin):
        """Admin puede crear roles."""
        response = client.post(
            "/api/v1/roles/",
            headers=headers_admin,
            json={"nombre": "nuevo_rol", "descripcion": "Descripción"}
        )

        assert response.status_code == 201

    def test_admin_puede_eliminar_ligas(self, client, headers_admin, liga_ejemplo):
        """Admin puede eliminar ligas."""
        response = client.delete(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_admin_puede_eliminar_equipos(self, client, headers_admin, equipo_ejemplo):
        """Admin puede eliminar equipos."""
        response = client.delete(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers=headers_admin
        )

        assert response.status_code == 204


# ============================================================
# PERMISOS DE COACH
# ============================================================

class TestPermisosCoach:
    """Tests para permisos de entrenador (coach)."""

    @pytest.fixture
    def usuario_coach(self, db, usuario_ejemplo, rol_coach):
        """Crea un usuario con rol coach."""
        usuario_rol = UsuarioRol(
            id_usuario=usuario_ejemplo.id_usuario,
            id_rol=rol_coach.id_rol
        )
        db.add(usuario_rol)
        db.commit()
        db.refresh(usuario_ejemplo)
        return usuario_ejemplo

    @pytest.fixture
    def token_coach(self, client, usuario_coach):
        """Token para usuario con rol coach."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": usuario_coach.email,
                "password": "password123"
            }
        )
        return response.json()["access_token"]

    @pytest.fixture
    def headers_coach(self, token_coach):
        """Headers con autorización para coach."""
        return {"Authorization": f"Bearer {token_coach}"}

    def test_coach_puede_ver_ligas(self, client, headers_coach, liga_ejemplo):
        """Coach puede ver ligas."""
        response = client.get(
            "/api/v1/ligas/",
            headers=headers_coach
        )

        assert response.status_code == 200

    def test_coach_no_puede_crear_ligas(self, client, headers_coach, datos_liga_nueva):
        """Coach no puede crear ligas."""
        response = client.post(
            "/api/v1/ligas/",
            headers=headers_coach,
            json=datos_liga_nueva
        )

        assert response.status_code == 403

    def test_coach_no_puede_eliminar_ligas(self, client, headers_coach, liga_ejemplo):
        """Coach no puede eliminar ligas."""
        response = client.delete(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers=headers_coach
        )

        assert response.status_code == 403


# ============================================================
# PERMISOS DE PLAYER
# ============================================================

class TestPermisosPlayer:
    """Tests para permisos de jugador (player)."""

    @pytest.fixture
    def usuario_player(self, db, usuario_ejemplo, rol_player):
        """Crea un usuario con rol player."""
        usuario_rol = UsuarioRol(
            id_usuario=usuario_ejemplo.id_usuario,
            id_rol=rol_player.id_rol
        )
        db.add(usuario_rol)
        db.commit()
        db.refresh(usuario_ejemplo)
        return usuario_ejemplo

    @pytest.fixture
    def token_player(self, client, usuario_player):
        """Token para usuario con rol player."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": usuario_player.email,
                "password": "password123"
            }
        )
        return response.json()["access_token"]

    @pytest.fixture
    def headers_player(self, token_player):
        """Headers con autorización para player."""
        return {"Authorization": f"Bearer {token_player}"}

    def test_player_puede_ver_ligas(self, client, headers_player, liga_ejemplo):
        """Player puede ver ligas."""
        response = client.get(
            "/api/v1/ligas/",
            headers=headers_player
        )

        assert response.status_code == 200

    def test_player_puede_ver_equipos(self, client, headers_player, equipo_ejemplo):
        """Player puede ver equipos."""
        response = client.get(
            "/api/v1/equipos/",
            headers=headers_player
        )

        assert response.status_code == 200

    def test_player_no_puede_crear_equipos(self, client, headers_player, datos_equipo_nuevo):
        """Player no puede crear equipos."""
        response = client.post(
            "/api/v1/equipos/",
            headers=headers_player,
            json=datos_equipo_nuevo
        )

        assert response.status_code == 403

    def test_player_no_puede_eliminar_equipos(self, client, headers_player, equipo_ejemplo):
        """Player no puede eliminar equipos."""
        response = client.delete(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers=headers_player
        )

        assert response.status_code == 403


# ============================================================
# PERMISOS DE VIEWER
# ============================================================

class TestPermisosViewer:
    """Tests para permisos de visualizador (viewer)."""

    @pytest.fixture
    def usuario_viewer(self, db, usuario_ejemplo):
        """Crea un usuario con rol viewer."""
        from app.models.rol import Rol

        rol = db.query(Rol).filter(Rol.nombre == "viewer").first()
        if not rol:
            rol = Rol(nombre="viewer", descripcion="Visualizador")
            db.add(rol)
            db.commit()
            db.refresh(rol)

        usuario_rol = UsuarioRol(
            id_usuario=usuario_ejemplo.id_usuario,
            id_rol=rol.id_rol
        )
        db.add(usuario_rol)
        db.commit()
        db.refresh(usuario_ejemplo)
        return usuario_ejemplo

    @pytest.fixture
    def token_viewer(self, client, usuario_viewer):
        """Token para usuario con rol viewer."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": usuario_viewer.email,
                "password": "password123"
            }
        )
        return response.json()["access_token"]

    @pytest.fixture
    def headers_viewer(self, token_viewer):
        """Headers con autorización para viewer."""
        return {"Authorization": f"Bearer {token_viewer}"}

    def test_viewer_puede_ver_ligas(self, client, headers_viewer, liga_ejemplo):
        """Viewer puede ver ligas."""
        response = client.get(
            "/api/v1/ligas/",
            headers=headers_viewer
        )

        assert response.status_code == 200

    def test_viewer_puede_ver_equipos(self, client, headers_viewer, equipo_ejemplo):
        """Viewer puede ver equipos."""
        response = client.get(
            "/api/v1/equipos/",
            headers=headers_viewer
        )

        assert response.status_code == 200

    def test_viewer_no_puede_crear_nada(self, client, headers_viewer):
        """Viewer no puede crear recursos."""
        # No puede crear ligas
        response = client.post(
            "/api/v1/ligas/",
            headers=headers_viewer,
            json={"nombre": "Liga", "temporada": "2024"}
        )
        assert response.status_code == 403

        # No puede crear equipos
        response = client.post(
            "/api/v1/equipos/",
            headers=headers_viewer,
            json={"nombre": "Equipo"}
        )
        assert response.status_code == 403

    def test_viewer_no_puede_eliminar_nada(self, client, headers_viewer, liga_ejemplo, equipo_ejemplo):
        """Viewer no puede eliminar recursos."""
        response = client.delete(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}",
            headers=headers_viewer
        )
        assert response.status_code == 403

        response = client.delete(
            f"/api/v1/equipos/{equipo_ejemplo.id_equipo}",
            headers=headers_viewer
        )
        assert response.status_code == 403


# ============================================================
# USUARIO SIN ROL
# ============================================================

class TestUsuarioSinRol:
    """Tests para usuario sin rol específico."""

    def test_usuario_sin_rol_puede_ver_recursos(self, client, token_usuario, liga_ejemplo, equipo_ejemplo):
        """Usuario sin rol puede ver recursos públicos."""
        # Puede ver ligas
        response = client.get(
            "/api/v1/ligas/",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )
        assert response.status_code == 200

        # Puede ver equipos
        response = client.get(
            "/api/v1/equipos/",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )
        assert response.status_code == 200

    def test_usuario_sin_rol_no_puede_crear(self, client, token_usuario, datos_liga_nueva):
        """Usuario sin rol no puede crear recursos administrativos."""
        response = client.post(
            "/api/v1/ligas/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json=datos_liga_nueva
        )

        assert response.status_code == 403


# ============================================================
# IMPORTACIONES NECESARIAS
# ============================================================

import pytest
from app.models.usuario_rol import UsuarioRol
from app.models.usuario_rol import UsuarioRol