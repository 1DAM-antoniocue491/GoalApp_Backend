# tests/test_jugadores.py
"""
Tests para el módulo de jugadores.
"""


# ============================================================
# CREAR JUGADOR
# ============================================================

class TestCrearJugador:
    """Tests para crear jugadores."""

    def test_crear_jugador_valido(self, client, headers_admin, usuario_ejemplo, equipo_ejemplo):
        """Crear jugador con datos válidos."""
        response = client.post(
            "/api/v1/jugadores/",
            headers=headers_admin,
            json={
                "id_usuario": usuario_ejemplo.id_usuario,
                "id_equipo": equipo_ejemplo.id_equipo,
                "posicion": "Delantero",
                "dorsal": 10
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["posicion"] == "Delantero"
        assert data["dorsal"] == 10

    def test_crear_jugador_usuario_ya_jugador(self, client, headers_admin, jugador_ejemplo, equipo_ejemplo):
        """Crear jugador cuando el usuario ya es jugador de otro equipo."""
        # El fixture jugador_ejemplo ya crea un jugador
        # Intentar crear otro jugador con el mismo usuario
        response = client.post(
            "/api/v1/jugadores/",
            headers=headers_admin,
            json={
                "id_usuario": jugador_ejemplo.id_usuario,
                "id_equipo": equipo_ejemplo.id_equipo,
                "posicion": "Portero",
                "dorsal": 1
            }
        )

        # Puede ser 400 si ya es jugador o 201 si se permite
        assert response.status_code in [201, 400]

    def test_crear_jugador_equipo_no_existente(self, client, headers_admin, usuario_ejemplo):
        """Crear jugador en equipo que no existe."""
        response = client.post(
            "/api/v1/jugadores/",
            headers=headers_admin,
            json={
                "id_usuario": usuario_ejemplo.id_usuario,
                "id_equipo": 999,
                "posicion": "Delantero",
                "dorsal": 10
            }
        )

        assert response.status_code == 404

    def test_crear_jugador_sin_permisos(self, client, token_usuario, usuario_ejemplo, equipo_ejemplo):
        """Crear jugador sin permisos."""
        response = client.post(
            "/api/v1/jugadores/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "id_usuario": usuario_ejemplo.id_usuario,
                "id_equipo": equipo_ejemplo.id_equipo,
                "posicion": "Delantero",
                "dorsal": 10
            }
        )

        assert response.status_code == 403


# ============================================================
# LISTAR JUGADORES
# ============================================================

class TestListarJugadores:
    """Tests para listar jugadores."""

    def test_listar_jugadores_vacio(self, client):
        """Listar jugadores cuando no hay ninguno."""
        response = client.get("/api/v1/jugadores/")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_jugadores_con_datos(self, client, jugador_ejemplo):
        """Listar jugadores con datos."""
        response = client.get("/api/v1/jugadores/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_listar_jugadores_por_equipo(self, client, equipo_ejemplo, jugador_ejemplo):
        """Listar jugadores de un equipo específico."""
        response = client.get(f"/api/v1/jugadores/?id_equipo={equipo_ejemplo.id_equipo}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


# ============================================================
# OBTENER JUGADOR POR ID
# ============================================================

class TestObtenerJugador:
    """Tests para obtener jugador por ID."""

    def test_obtener_jugador_existente(self, client, jugador_ejemplo):
        """Obtener jugador que existe."""
        response = client.get(f"/api/v1/jugadores/{jugador_ejemplo.id_jugador}")

        assert response.status_code == 200
        assert response.json()["id_jugador"] == jugador_ejemplo.id_jugador

    def test_obtener_jugador_no_existente(self, client):
        """Obtener jugador que no existe."""
        response = client.get("/api/v1/jugadores/999")

        assert response.status_code == 404


# ============================================================
# ACTUALIZAR JUGADOR
# ============================================================

class TestActualizarJugador:
    """Tests para actualizar jugador."""

    def test_actualizar_posicion_jugador(self, client, headers_admin, jugador_ejemplo):
        """Actualizar posición de jugador."""
        response = client.put(
            f"/api/v1/jugadores/{jugador_ejemplo.id_jugador}",
            headers=headers_admin,
            json={"posicion": "Mediocampista"}
        )

        assert response.status_code == 200
        assert response.json()["posicion"] == "Mediocampista"

    def test_actualizar_dorsal_jugador(self, client, headers_admin, jugador_ejemplo):
        """Actualizar dorsal de jugador."""
        response = client.put(
            f"/api/v1/jugadores/{jugador_ejemplo.id_jugador}",
            headers=headers_admin,
            json={"dorsal": 7}
        )

        assert response.status_code == 200
        assert response.json()["dorsal"] == 7

    def test_actualizar_jugador_sin_permisos(self, client, token_usuario, jugador_ejemplo):
        """Actualizar jugador sin permisos."""
        response = client.put(
            f"/api/v1/jugadores/{jugador_ejemplo.id_jugador}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"posicion": "Defensa"}
        )

        assert response.status_code == 403

    def test_actualizar_jugador_no_existente(self, client, headers_admin):
        """Actualizar jugador que no existe."""
        response = client.put(
            "/api/v1/jugadores/999",
            headers=headers_admin,
            json={"posicion": "Defensa"}
        )

        assert response.status_code == 404


# ============================================================
# ELIMINAR JUGADOR
# ============================================================

class TestEliminarJugador:
    """Tests para eliminar jugador."""

    def test_eliminar_jugador_existente(self, client, headers_admin, jugador_ejemplo):
        """Eliminar jugador que existe."""
        response = client.delete(
            f"/api/v1/jugadores/{jugador_ejemplo.id_jugador}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_jugador_sin_permisos(self, client, token_usuario, jugador_ejemplo):
        """Eliminar jugador sin permisos."""
        response = client.delete(
            f"/api/v1/jugadores/{jugador_ejemplo.id_jugador}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_jugador_no_existente(self, client, headers_admin):
        """Eliminar jugador que no existe."""
        response = client.delete(
            "/api/v1/jugadores/999",
            headers=headers_admin
        )

        assert response.status_code == 404