# tests/test_convocatorias.py
"""
Tests para el módulo de convocatorias de partido.
"""


# ============================================================
# CREAR CONVOCATORIA
# ============================================================

class TestCrearConvocatoria:
    """Tests para crear convocatorias."""

    def test_crear_convocatoria_valida(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Crear convocatoria con datos válidos."""
        response = client.post(
            "/api/v1/convocatorias/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "es_titular": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["es_titular"] == True

    def test_crear_convocatoria_suplente(self, client, headers_admin, partido_ejemplo, jugador_ejemplo):
        """Crear convocatoria como suplente."""
        response = client.post(
            "/api/v1/convocatorias/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "es_titular": False
            }
        )

        assert response.status_code == 201
        assert response.json()["es_titular"] == False

    def test_crear_convocatoria_sin_permisos(self, client, token_usuario, partido_ejemplo, jugador_ejemplo):
        """Crear convocatoria sin permisos."""
        response = client.post(
            "/api/v1/convocatorias/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "es_titular": True
            }
        )

        assert response.status_code == 403

    def test_crear_convocatoria_duplicada(self, client, headers_admin, partido_ejemplo, jugador_ejemplo, db):
        """Crear convocatoria duplicada (mismo jugador en mismo partido)."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        # Crear primera convocatoria
        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=True
        )
        db.add(convocatoria)
        db.commit()

        # Intentar crear duplicada
        response = client.post(
            "/api/v1/convocatorias/",
            headers=headers_admin,
            json={
                "id_partido": partido_ejemplo.id_partido,
                "id_jugador": jugador_ejemplo.id_jugador,
                "es_titular": False
            }
        )

        assert response.status_code == 400


# ============================================================
# LISTAR CONVOCATORIAS
# ============================================================

class TestListarConvocatorias:
    """Tests para listar convocatorias."""

    def test_listar_convocatorias_partido(self, client, headers_admin, partido_ejemplo, jugador_ejemplo, db):
        """Listar convocatorias de un partido."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        # Crear convocatoria
        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=True
        )
        db.add(convocatoria)
        db.commit()

        response = client.get(f"/api/v1/convocatorias/partido/{partido_ejemplo.id_partido}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_listar_convocatorias_partido_vacio(self, client, partido_ejemplo):
        """Listar convocatorias cuando no hay ninguna."""
        response = client.get(f"/api/v1/convocatorias/partido/{partido_ejemplo.id_partido}")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_convocatorias_partido_no_existente(self, client):
        """Listar convocatorias de partido que no existe."""
        response = client.get("/api/v1/convocatorias/partido/999")

        assert response.status_code == 404


# ============================================================
# ACTUALIZAR CONVOCATORIA
# ============================================================

class TestActualizarConvocatoria:
    """Tests para actualizar convocatoria."""

    def test_cambiar_a_titular(self, client, headers_admin, partido_ejemplo, jugador_ejemplo, db):
        """Cambiar jugador de suplente a titular."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        # Crear convocatoria como suplente
        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=False
        )
        db.add(convocatoria)
        db.commit()
        db.refresh(convocatoria)

        response = client.put(
            f"/api/v1/convocatorias/{convocatoria.id_convocatoria}",
            headers=headers_admin,
            json={"es_titular": True}
        )

        assert response.status_code == 200
        assert response.json()["es_titular"] == True

    def test_cambiar_a_suplente(self, client, headers_admin, partido_ejemplo, jugador_ejemplo, db):
        """Cambiar jugador de titular a suplente."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        # Crear convocatoria como titular
        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=True
        )
        db.add(convocatoria)
        db.commit()
        db.refresh(convocatoria)

        response = client.put(
            f"/api/v1/convocatorias/{convocatoria.id_convocatoria}",
            headers=headers_admin,
            json={"es_titular": False}
        )

        assert response.status_code == 200
        assert response.json()["es_titular"] == False

    def test_actualizar_convocatoria_sin_permisos(self, client, token_usuario, partido_ejemplo, jugador_ejemplo, db):
        """Actualizar convocatoria sin permisos."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=True
        )
        db.add(convocatoria)
        db.commit()
        db.refresh(convocatoria)

        response = client.put(
            f"/api/v1/convocatorias/{convocatoria.id_convocatoria}",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"es_titular": False}
        )

        assert response.status_code == 403


# ============================================================
# ELIMINAR CONVOCATORIA
# ============================================================

class TestEliminarConvocatoria:
    """Tests para eliminar convocatoria."""

    def test_eliminar_convocatoria_existente(self, client, headers_admin, partido_ejemplo, jugador_ejemplo, db):
        """Eliminar convocatoria que existe."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=True
        )
        db.add(convocatoria)
        db.commit()
        db.refresh(convocatoria)

        response = client.delete(
            f"/api/v1/convocatorias/{convocatoria.id_convocatoria}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_convocatoria_sin_permisos(self, client, token_usuario, partido_ejemplo, jugador_ejemplo, db):
        """Eliminar convocatoria sin permisos."""
        from app.models.convocatoria_partido import ConvocatoriaPartido

        convocatoria = ConvocatoriaPartido(
            id_partido=partido_ejemplo.id_partido,
            id_jugador=jugador_ejemplo.id_jugador,
            es_titular=True
        )
        db.add(convocatoria)
        db.commit()
        db.refresh(convocatoria)

        response = client.delete(
            f"/api/v1/convocatorias/{convocatoria.id_convocatoria}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_convocatoria_no_existente(self, client, headers_admin):
        """Eliminar convocatoria que no existe."""
        response = client.delete(
            "/api/v1/convocatorias/999",
            headers=headers_admin
        )

        assert response.status_code == 404