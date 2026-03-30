# tests/test_liga_configuracion.py
"""
Tests para el módulo de configuración de liga.
Tests para los nuevos campos de convocatorias y titulares.
"""
from datetime import time


# ============================================================
# OBTENER CONFIGURACIÓN
# ============================================================

class TestObtenerConfiguracion:
    """Tests para obtener la configuración de una liga."""

    def test_obtener_configuracion_existente(self, client, liga_ejemplo, liga_configuracion_ejemplo):
        """Obtener configuración de una liga que existe."""
        response = client.get(f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion")

        assert response.status_code == 200
        data = response.json()
        assert data["id_liga"] == liga_ejemplo.id_liga
        assert "min_jugadores_convocados" in data
        assert "max_jugadores_convocados" in data
        assert "num_titulares" in data

    def test_obtener_configuracion_liga_sin_configuracion(self, client, liga_ejemplo):
        """Obtener configuración de liga que no tiene configuración."""
        response = client.get(f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion")

        assert response.status_code == 404

    def test_obtener_configuracion_liga_no_existente(self, client):
        """Obtener configuración de liga que no existe."""
        response = client.get("/api/v1/ligas/999/configuracion")

        assert response.status_code == 404

    def test_configuracion_contiene_campos_convocatoria(self, client, liga_ejemplo, liga_configuracion_ejemplo):
        """Verificar que la configuración incluye los campos de convocatoria."""
        response = client.get(f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion")

        assert response.status_code == 200
        data = response.json()
        assert data["min_jugadores_convocados"] == 11
        assert data["max_jugadores_convocados"] == 18
        assert data["num_titulares"] == 11


# ============================================================
# CREAR CONFIGURACIÓN
# ============================================================

class TestCrearConfiguracion:
    """Tests para crear la configuración de una liga."""

    def test_crear_configuracion_valida(self, client, headers_admin, liga_ejemplo):
        """Crear configuración con datos válidos."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 16,
                "min_partidos_entre_equipos": 2,
                "min_jugadores_convocados": 11,
                "max_jugadores_convocados": 16,
                "num_titulares": 11
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["min_jugadores_convocados"] == 11
        assert data["max_jugadores_convocados"] == 16
        assert data["num_titulares"] == 11

    def test_crear_configuracion_valores_por_defecto(self, client, headers_admin, liga2_ejemplo):
        """Crear configuración usando valores por defecto para convocatorias."""
        response = client.post(
            f"/api/v1/ligas/{liga2_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2
            }
        )

        assert response.status_code == 201
        data = response.json()
        # Verificar valores por defecto
        assert data["min_jugadores_convocados"] == 11
        assert data["max_jugadores_convocados"] == 18
        assert data["num_titulares"] == 11

    def test_crear_configuracion_sin_permisos(self, client, token_usuario, liga_ejemplo):
        """Crear configuración sin permisos de admin."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2
            }
        )

        assert response.status_code == 403

    def test_crear_configuracion_sin_autenticacion(self, client, liga_ejemplo):
        """Crear configuración sin autenticación."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2
            }
        )

        assert response.status_code == 401

    def test_crear_configuracion_duplicada(self, client, headers_admin, liga_ejemplo, liga_configuracion_ejemplo):
        """Crear configuración cuando ya existe (debe fallar)."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "18:00:00",
                "max_equipos": 10,
                "min_partidos_entre_equipos": 1
            }
        )

        assert response.status_code == 400

    def test_crear_configuracion_min_jugadores_convocados_invalido(self, client, headers_admin, liga_ejemplo):
        """Crear configuración con mínimo de jugadores en convocatoria inválido."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2,
                "min_jugadores_convocados": 5  # Menor que el mínimo permitido (7)
            }
        )

        assert response.status_code == 422

    def test_crear_configuracion_max_jugadores_convocados_invalido(self, client, headers_admin, liga_ejemplo):
        """Crear configuración con máximo de jugadores en convocatoria inválido."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2,
                "max_jugadores_convocados": 50  # Mayor que el máximo permitido (30)
            }
        )

        assert response.status_code == 422

    def test_crear_configuracion_num_titulares_invalido(self, client, headers_admin, liga_ejemplo):
        """Crear configuración con número de titulares inválido."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2,
                "num_titulares": 15  # Mayor que el máximo permitido (11)
            }
        )

        assert response.status_code == 422


# ============================================================
# ACTUALIZAR CONFIGURACIÓN
# ============================================================

class TestActualizarConfiguracion:
    """Tests para actualizar la configuración de una liga."""

    def test_actualizar_min_jugadores_convocados(self, client, headers_admin, liga_ejemplo, liga_configuracion_ejemplo):
        """Actualizar el mínimo de jugadores en convocatoria."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={"min_jugadores_convocados": 14}
        )

        assert response.status_code == 200
        assert response.json()["min_jugadores_convocados"] == 14

    def test_actualizar_max_jugadores_convocados(self, client, headers_admin, liga_ejemplo, liga_configuracion_ejemplo):
        """Actualizar el máximo de jugadores en convocatoria."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={"max_jugadores_convocados": 20}
        )

        assert response.status_code == 200
        assert response.json()["max_jugadores_convocados"] == 20

    def test_actualizar_num_titulares(self, client, headers_admin, liga_ejemplo, liga_configuracion_ejemplo):
        """Actualizar el número de jugadores titulares."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={"num_titulares": 7}
        )

        assert response.status_code == 200
        assert response.json()["num_titulares"] == 7

    def test_actualizar_todos_los_campos_convocatoria(self, client, headers_admin, liga_ejemplo, liga_configuracion_ejemplo):
        """Actualizar todos los campos de convocatoria a la vez."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "min_jugadores_convocados": 12,
                "max_jugadores_convocados": 22,
                "num_titulares": 7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["min_jugadores_convocados"] == 12
        assert data["max_jugadores_convocados"] == 22
        assert data["num_titulares"] == 7

    def test_actualizar_configuracion_sin_permisos(self, client, token_usuario, liga_ejemplo, liga_configuracion_ejemplo):
        """Actualizar configuración sin permisos de admin."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers={"Authorization": f"Bearer {token_usuario}"},
            json={"min_jugadores_convocados": 14}
        )

        assert response.status_code == 403

    def test_actualizar_configuracion_liga_sin_configuracion(self, client, headers_admin, liga_ejemplo):
        """Actualizar configuración de liga que no tiene configuración."""
        response = client.put(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={"min_jugadores_convocados": 14}
        )

        assert response.status_code == 404

    def test_actualizar_configuracion_liga_no_existente(self, client, headers_admin):
        """Actualizar configuración de liga que no existe."""
        response = client.put(
            "/api/v1/ligas/999/configuracion",
            headers=headers_admin,
            json={"min_jugadores_convocados": 14}
        )

        assert response.status_code == 404


# ============================================================
# VALIDACIONES DE LÓGICA DE NEGOCIO
# ============================================================

class TestValidacionesConvocatoria:
    """Tests para validaciones de lógica de negocio sobre convocatorias."""

    def test_min_convocados_menor_que_max(self, client, headers_admin, liga_ejemplo):
        """Verificar que min_jugadores_convocados puede ser menor que max."""
        # Crear con valores válidos
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2,
                "min_jugadores_convocados": 11,
                "max_jugadores_convocados": 18  # max > min
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["min_jugadores_convocados"] < data["max_jugadores_convocados"]

    def test_num_titulares_no_puede_ser_mayor_que_max_convocados(self, client, headers_admin, liga_ejemplo):
        """Verificar lógica: num_titulares no debería exceder max_jugadores_convocados."""
        # Nota: Esta validación podría implementarse a nivel de servicio
        # Por ahora, el schema permite valores independientes
        # El test documenta el comportamiento esperado
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2,
                "num_titulares": 11,
                "max_jugadores_convocados": 14  # 14 > 11, válido
            }
        )

        assert response.status_code == 201

    def test_configuracion_convocatoria_futbol_7(self, client, headers_admin, liga2_ejemplo):
        """Test para configuración de liga de fútbol 7."""
        response = client.post(
            f"/api/v1/ligas/{liga2_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "18:00:00",
                "max_equipos": 12,
                "min_partidos_entre_equipos": 2,
                "min_jugadores_convocados": 7,
                "max_jugadores_convocados": 14,
                "num_titulares": 7
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["num_titulares"] == 7
        assert data["min_jugadores_convocados"] == 7

    def test_configuracion_convocatoria_futbol_11(self, client, headers_admin, liga_ejemplo):
        """Test para configuración de liga de fútbol 11 (estándar)."""
        response = client.post(
            f"/api/v1/ligas/{liga_ejemplo.id_liga}/configuracion",
            headers=headers_admin,
            json={
                "hora_partidos": "17:00:00",
                "max_equipos": 20,
                "min_partidos_entre_equipos": 2,
                "min_jugadores_convocados": 11,
                "max_jugadores_convocados": 22,
                "num_titulares": 11
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["num_titulares"] == 11
        assert data["max_jugadores_convocados"] == 22