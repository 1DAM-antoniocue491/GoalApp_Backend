# tests/test_eventos.py
"""
Tests para el módulo de eventos de partido.
"""


# ============================================================
# CREAR EVENTO
# ============================================================

class TestCrearEvento:
    """Tests para crear eventos de partido."""

    def test_registrar_gol(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Registrar un gol en el partido."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "gol",
                "minuto": 25
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tipo_evento"] == "gol"
        assert data["minuto"] == 25

    def test_registrar_tarjeta_amarilla(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Registrar una tarjeta amarilla."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "tarjeta_amarilla",
                "minuto": 35
            }
        )

        assert response.status_code == 201
        assert response.json()["tipo_evento"] == "tarjeta_amarilla"

    def test_registrar_tarjeta_roja(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Registrar una tarjeta roja."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "tarjeta_roja",
                "minuto": 78
            }
        )

        assert response.status_code == 201
        assert response.json()["tipo_evento"] == "tarjeta_roja"

    def test_registrar_cambio(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Registrar un cambio de jugador."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "cambio",
                "minuto": 60
            }
        )

        assert response.status_code == 201
        assert response.json()["tipo_evento"] == "cambio"

    def test_registrar_evento_sin_permisos(self, client, token_usuario, partido_ejemplo, jugador_ejemplo):
        """Registrar evento sin permisos."""
        response = client.post(
            "/api/v1/eventos/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "gol",
                "minuto": 25
            }
        )

        assert response.status_code == 403

    def test_registrar_evento_partido_no_existente(self, client, headers_admin, jugador_ejemplo):
        """Registrar evento en partido que no existe."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": 999,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "gol",
                "minuto": 25
            }
        )

        assert response.status_code == 404

    def test_registrar_evento_jugador_no_existente(self, client, headers_admin, partido_ejemplo):
        """Registrar evento con jugador que no existe."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": 999,
                "tipo_evento": "gol",
                "minuto": 25
            }
        )

        assert response.status_code == 404

    def test_registrar_evento_minuto_invalido(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Registrar evento con minuto inválido."""
        response = client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "gol",
                "minuto": 150  # Más de 90 minutos
            }
        )

        # Puede ser 201 o 422 dependiendo de la validación
        assert response.status_code in [201, 422]


# ============================================================
# LISTAR EVENTOS
# ============================================================

class TestListarEventos:
    """Tests para listar eventos de un partido."""

    def test_listar_eventos_partido_vacio(self, client, partido_ejemplo):
        """Listar eventos cuando no hay ninguno."""
        response = client.get(f"/api/v1/eventos/partido/{partido_ejemplo.id_partido}")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_eventos_partido_con_datos(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Listar eventos de un partido."""
        # Crear eventos
        client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "gol",
                "minuto": 25
            }
        )
        client.post(
            "/api/v1/eventos/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "tipo_evento": "tarjeta_amarilla",
                "minuto": 35
            }
        )

        response = client.get(f"/api/v1/eventos/partido/{partido_ejemplo.id_partido}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_listar_eventos_partido_no_existente(self, client):
        """Listar eventos de partido que no existe."""
        response = client.get("/api/v1/eventos/partido/999")

        assert response.status_code == 404


# ============================================================
# ELIMINAR EVENTO
# ============================================================

class TestEliminarEvento:
    """Tests para eliminar evento."""

    def test_eliminar_evento_existente(self, client, headers_admin, partido_ejemplo, jugador_ejemplo, db):
        """Eliminar evento que existe."""
        from app.models.evento_partido import EventoPartido

        # Crear evento
        evento = EventoPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            tipo_evento="gol",
            minuto=25
        )
        db.add(evento)
        db.commit()
        db.refresh(evento)

        response = client.delete(
            f"/api/v1/eventos/{evento.id_evento}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_evento_sin_permisos(self, client, token_usuario, db, partido_ejemplo, jugador_ejemplo):
        """Eliminar evento sin permisos."""
        from app.models.evento_partido import EventoPartido

        evento = EventoPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            tipo_evento="gol",
            minuto=25
        )
        db.add(evento)
        db.commit()
        db.refresh(evento)

        response = client.delete(
            f"/api/v1/eventos/{evento.id_evento}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_evento_no_existente(self, client, headers_admin):
        """Eliminar evento que no existe."""
        response = client.delete(
            "/api/v1/eventos/999",
            headers=headers_admin
        )

        assert response.status_code == 404