# tests/test_formaciones.py
"""
Tests para el módulo de formaciones.
"""


# ============================================================
# CREAR FORMACIÓN
# ============================================================

class TestCrearFormacion:
    """Tests para crear formaciones."""

    def test_crear_formacion_valida(self, client, headers_admin):
        """Crear formación con datos válidos."""
        response = client.post(
            "/api/v1/formaciones/",
            headers=headers_admin,
            json={
                "nombre": "4-4-2",
                "descripcion": "Formación clásica"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "4-4-2"

    def test_crear_formacion_sin_permisos(self, client, token_usuario):
        """Crear formación sin permisos."""
        response = client.post(
            "/api/v1/formaciones/",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "nombre": "4-3-3",
                "descripcion": "Formación ofensiva"
            }
        )

        assert response.status_code == 403

    def test_crear_formacion_nombre_vacio(self, client, headers_admin):
        """Crear formación con nombre vacío."""
        response = client.post(
            "/api/v1/formaciones/",
            headers=headers_admin,
            json={
                "nombre": "",
                "descripcion": "Sin nombre"
            }
        )

        assert response.status_code == 422


# ============================================================
# LISTAR FORMACIONES
# ============================================================

class TestListarFormaciones:
    """Tests para listar formaciones."""

    def test_listar_formaciones_vacio(self, client):
        """Listar formaciones cuando no hay ninguna."""
        response = client.get("/api/v1/formaciones/")

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_formaciones_con_datos(self, client, headers_admin):
        """Listar formaciones con datos."""
        # Crear formación
        client.post(
            "/api/v1/formaciones/",
            headers=headers_admin,
            json={"nombre": "4-4-2", "descripcion": "Clásica"}
        )

        response = client.get("/api/v1/formaciones/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


# ============================================================
# OBTENER FORMACIÓN POR ID
# ============================================================

class TestObtenerFormacion:
    """Tests para obtener formación por ID."""

    def test_obtener_formacion_existente(self, client, headers_admin, db):
        """Obtener formación que existe."""
        from app.models.formacion import Formacion

        formacion = Formacion(nombre="4-4-2", descripcion="Clásica")
        db.add(formacion)
        db.commit()
        db.refresh(formacion)

        response = client.get(f"/api/v1/formaciones/{formacion.id_formacion}")

        assert response.status_code == 200
        assert response.json()["nombre"] == "4-4-2"

    def test_obtener_formacion_no_existente(self, client):
        """Obtener formación que no existe."""
        response = client.get("/api/v1/formaciones/999")

        assert response.status_code == 404


# ============================================================
# ELIMINAR FORMACIÓN
# ============================================================

class TestEliminarFormacion:
    """Tests para eliminar formación."""

    def test_eliminar_formacion_existente(self, client, headers_admin, db):
        """Eliminar formación que existe."""
        from app.models.formacion import Formacion

        formacion = Formacion(nombre="4-4-2", descripcion="Clásica")
        db.add(formacion)
        db.commit()
        db.refresh(formacion)

        response = client.delete(
            f"/api/v1/formaciones/{formacion.id_formacion}",
            headers=headers_admin
        )

        assert response.status_code == 204

    def test_eliminar_formacion_sin_permisos(self, client, token_usuario, db):
        """Eliminar formación sin permisos."""
        from app.models.formacion import Formacion

        formacion = Formacion(nombre="4-3-3", descripcion="Ofensiva")
        db.add(formacion)
        db.commit()
        db.refresh(formacion)

        response = client.delete(
            f"/api/v1/formaciones/{formacion.id_formacion}",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403

    def test_eliminar_formacion_no_existente(self, client, headers_admin):
        """Eliminar formación que no existe."""
        response = client.delete(
            "/api/v1/formaciones/999",
            headers=headers_admin
        )

        assert response.status_code == 404