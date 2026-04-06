# tests/shared/helpers.py
"""
Funciones auxiliares para tests.
"""
import uuid
from datetime import datetime


def generate_unique_email(domain: str = "test.com") -> str:
    """Genera un email unico para tests."""
    return f"test_{uuid.uuid4().hex[:8]}@{domain}"


def generate_unique_name(prefix: str = "Test") -> str:
    """Genera un nombre unico para tests."""
    return f"{prefix} {uuid.uuid4().hex[:8]}"


def format_datetime_for_api(dt: datetime) -> str:
    """Formatea un datetime para enviar a la API."""
    return dt.isoformat()


def parse_datetime_from_api(dt_str: str) -> datetime:
    """Parsea un datetime desde la respuesta de la API."""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


class TestDataCleaner:
    """Helper para limpiar datos creados durante tests de integracion."""

    def __init__(self, api_client):
        self.api_client = api_client
        self.created_entities = []

    def track(self, entity_type: str, entity_id: int):
        """Registra una entidad creada para limpiar despues."""
        self.created_entities.append((entity_type, entity_id))

    def cleanup(self):
        """Elimina todas las entidades registradas en orden inverso."""
        for entity_type, entity_id in reversed(self.created_entities):
            try:
                self.api_client.delete(f"/{entity_type}/{entity_id}")
            except Exception:
                pass  # Ignorar errores de limpieza
        self.created_entities.clear()