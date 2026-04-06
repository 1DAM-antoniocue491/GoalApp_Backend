# tests/test_public.py
"""
Tests para endpoints públicos (sin autenticación).
"""


# ============================================================
# ENDPOINTS PÚBLICOS DE LIGAS
# ============================================================

class TestPublicLigas:
    """Tests para endpoints públicos de ligas."""

    def test_listar_ligas_publico(self, client, liga_ejemplo):
        """Listar ligas sin autenticación."""
        response = client.get("/api/v1/public/ligas/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_ver_liga_publico(self, client, liga_ejemplo):
        """Ver detalles de liga sin autenticación."""
        response = client.get(f"/api/v1/public/ligas/{liga_ejemplo.id_liga}")

        assert response.status_code == 200
        assert response.json()["id_liga"] == liga_ejemplo.id_liga

    def test_ver_liga_no_existente_publico(self, client):
        """Ver liga que no existe sin autenticación."""
        response = client.get("/api/v1/public/ligas/999")

        assert response.status_code == 404


# ============================================================
# ENDPOINTS PÚBLICOS DE CLASIFICACIÓN
# ============================================================

class TestPublicClasificacion:
    """Tests para clasificación pública."""

    def test_ver_clasificacion_publico(self, client, liga_ejemplo, equipo_ejemplo):
        """Ver clasificación sin autenticación."""
        response = client.get(f"/api/v1/public/ligas/{liga_ejemplo.id_liga}/clasificacion")

        assert response.status_code == 200
        # Puede estar vacía si no hay partidos
        assert isinstance(response.json(), list)

    def test_ver_clasificacion_liga_no_existente(self, client):
        """Ver clasificación de liga que no existe."""
        response = client.get("/api/v1/public/ligas/999/clasificacion")

        assert response.status_code == 404


# ============================================================
# ENDPOINTS PÚBLICOS DE JORNADAS
# ============================================================

class TestPublicJornadas:
    """Tests para jornadas públicas."""

    def test_ver_jornadas_publico(self, client, liga_ejemplo, partido_ejemplo):
        """Ver jornadas sin autenticación."""
        response = client.get(f"/api/v1/public/ligas/{liga_ejemplo.id_liga}/jornadas")

        assert response.status_code == 200

    def test_ver_jornadas_liga_no_existente(self, client):
        """Ver jornadas de liga que no existe."""
        response = client.get("/api/v1/public/ligas/999/jornadas")

        assert response.status_code == 404


# ============================================================
# ENDPOINTS PÚBLICOS DE EQUIPOS
# ============================================================

class TestPublicEquipos:
    """Tests para endpoints públicos de equipos."""

    def test_listar_equipos_publico(self, client, equipo_ejemplo):
        """Listar equipos sin autenticación."""
        response = client.get("/api/v1/public/equipos/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_ver_equipo_publico(self, client, equipo_ejemplo):
        """Ver detalles de equipo sin autenticación."""
        response = client.get(f"/api/v1/public/equipos/{equipo_ejemplo.id_equipo}")

        assert response.status_code == 200
        assert response.json()["id_equipo"] == equipo_ejemplo.id_equipo

    def test_ver_equipo_no_existente_publico(self, client):
        """Ver equipo que no existe sin autenticación."""
        response = client.get("/api/v1/public/equipos/999")

        assert response.status_code == 404


# ============================================================
# ENDPOINTS PÚBLICOS DE PARTIDOS
# ============================================================

class TestPublicPartidos:
    """Tests para endpoints públicos de partidos."""

    def test_listar_partidos_publico(self, client, partido_ejemplo):
        """Listar partidos sin autenticación."""
        response = client.get("/api/v1/public/partidos/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_ver_partido_publico(self, client, partido_ejemplo):
        """Ver detalles de partido sin autenticación."""
        response = client.get(f"/api/v1/public/partidos/{partido_ejemplo.id_partido}")

        assert response.status_code == 200
        assert response.json()["id_partido"] == partido_ejemplo.id_partido

    def test_ver_partido_no_existente_publico(self, client):
        """Ver partido que no existe sin autenticación."""
        response = client.get("/api/v1/public/partidos/999")

        assert response.status_code == 404


# ============================================================
# VERIFICACIÓN DE AUTENTICACIÓN
# ============================================================

class TestAutenticacionRequerida:
    """Tests para verificar que endpoints protegidos requieren autenticación."""

    def test_crear_liga_sin_autenticacion(self, client, datos_liga_nueva):
        """Crear liga sin autenticación debe fallar."""
        response = client.post(
            "/api/v1/ligas/",
            json=datos_liga_nueva
        )

        assert response.status_code == 401

    def test_crear_usuario_sin_autenticacion(self, client):
        """Registrar usuario público (permitido)."""
        response = client.post(
            "/api/v1/usuarios/",
            json={
                "nombre": "Usuario Público",
                "email": "publico@email.com",
                "password": "password123"
            }
        )

        # Crear usuario está permitido sin autenticación
        assert response.status_code == 201

    def test_actualizar_usuario_sin_autenticacion(self, client, usuario_ejemplo):
        """Actualizar usuario sin autenticación debe fallar."""
        response = client.put(
            f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}",
            json={"nombre": "Nuevo Nombre"}
        )

        assert response.status_code == 401

    def test_eliminar_usuario_sin_autenticacion(self, client, usuario_ejemplo):
        """Eliminar usuario sin autenticación debe fallar."""
        response = client.delete(f"/api/v1/usuarios/{usuario_ejemplo.id_usuario}")

        assert response.status_code == 401

    def test_crear_equipo_sin_autenticacion(self, client, datos_equipo_nuevo):
        """Crear equipo sin autenticación debe fallar."""
        response = client.post(
            "/api/v1/equipos/",
            json=datos_equipo_nuevo
        )

        assert response.status_code == 401

    def test_crear_partido_sin_autenticacion(self, client):
        """Crear partido sin autenticación debe fallar."""
        response = client.post(
            "/api/v1/partidos/",
            json={
                "id_liga": 1,
                "id_equipo_local": 1,
                "id_equipo_visitante": 2,
                "fecha": "2024-12-31",
                "estado": "programado"
            }
        )

        assert response.status_code == 401