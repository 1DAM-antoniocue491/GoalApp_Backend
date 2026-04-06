# app/models/evento_partido.py
"""
Modelo de Evento de Partido para registrar incidencias del juego.
Almacena goles, tarjetas, cambios y otros eventos del partido.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class EventoPartido(Base):
    """
    Modelo ORM para la tabla 'eventos_partido'.

    Registra todos los eventos que ocurren durante un partido:
    - Goles
    - Tarjetas amarillas/rojas
    - Cambios de jugadores
    - MVP (Jugador destacado)

    Attributes:
        id_evento (int): Identificador único del evento (Primary Key)
        id_partido (int): ID del partido donde ocurrió (Foreign Key)
        id_jugador (int): ID del jugador involucrado (Foreign Key)
        tipo_evento (str): Tipo de evento (ej: "Gol", "Tarjeta Amarilla", máx. 50 caracteres)
        minuto (int): Minuto del partido en que ocurrió el evento
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        partido (Partido): Relación con el partido
        jugador (Jugador): Relación con el jugador
    """
    __tablename__ = "eventos_partido"

    # Clave primaria
    id_evento = Column(Integer, primary_key=True)

    # Relaciones: partido y jugador involucrado
    id_partido = Column(Integer, ForeignKey("partidos.id_partido"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("jugadores.id_jugador"), nullable=False)

    # Información del evento
    tipo_evento = Column(String(50), nullable=False)  # Ejemplo: "Gol", "Tarjeta Amarilla", "Tarjeta Roja", "Cambio", "MVP"
    minuto = Column(Integer, nullable=False)  # Minuto en que ocurrió (0-90+)

    # Auditoría: fechas de creación y actualización
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    partido = relationship("Partido", lazy="selectin")
    jugador = relationship("Jugador", lazy="selectin")
