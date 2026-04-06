# tests/shared/factories.py
"""
Factorias para crear entidades de prueba.
Usa el patron Factory para generar datos consistentes.
"""
import uuid
from datetime import datetime, timedelta


class UserFactory:
    """Factoria para crear usuarios de prueba."""

    @staticmethod
    def create(nombre: str = None, email: str = None, password: str = "password123"):
        """Crea un diccionario con datos de usuario."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "nombre": nombre or f"Usuario Test {unique_id}",
            "email": email or f"test_{unique_id}@email.com",
            "password": password
        }

    @staticmethod
    def create_admin(email: str = None):
        """Crea un diccionario con datos de usuario admin."""
        data = UserFactory.create(email=email)
        data["nombre"] = f"Admin Test {uuid.uuid4().hex[:8]}"
        return data


class TeamFactory:
    """Factoria para crear equipos de prueba."""

    @staticmethod
    def create(nombre: str = None, id_liga: int = None,
               id_entrenador: int = None, id_delegado: int = None):
        """Crea un diccionario con datos de equipo."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "nombre": nombre or f"Equipo Test {unique_id}",
            "id_liga": id_liga,
            "id_entrenador": id_entrenador,
            "id_delegado": id_delegado
        }


class LeagueFactory:
    """Factoria para crear ligas de prueba."""

    @staticmethod
    def create(nombre: str = None, temporada: str = None):
        """Crea un diccionario con datos de liga."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "nombre": nombre or f"Liga Test {unique_id}",
            "temporada": temporada or "2025-2026"
        }


class MatchFactory:
    """Factoria para crear partidos de prueba."""

    @staticmethod
    def create(id_liga: int, id_equipo_local: int, id_equipo_visitante: int,
               fecha: datetime = None, estado: str = "programado"):
        """Crea un diccionario con datos de partido."""
        return {
            "id_liga": id_liga,
            "id_equipo_local": id_equipo_local,
            "id_equipo_visitante": id_equipo_visitante,
            "fecha": (fecha or datetime.utcnow() + timedelta(days=7)).isoformat(),
            "estado": estado
        }


class PlayerFactory:
    """Factoria para crear jugadores de prueba."""

    @staticmethod
    def create(id_usuario: int, id_equipo: int,
               posicion: str = "Delantero", dorsal: int = None):
        """Crea un diccionario con datos de jugador."""
        return {
            "id_usuario": id_usuario,
            "id_equipo": id_equipo,
            "posicion": posicion,
            "dorsal": dorsal or 10
        }


class NotificationFactory:
    """Factoria para crear notificaciones de prueba."""

    @staticmethod
    def create(id_usuario: int, mensaje: str = None):
        """Crea un diccionario con datos de notificacion."""
        unique_id = uuid.uuid4().hex[:8]
        return {
            "id_usuario": id_usuario,
            "mensaje": mensaje or f"Notificacion de prueba {unique_id}"
        }