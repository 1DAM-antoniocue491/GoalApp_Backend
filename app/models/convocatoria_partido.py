# app/models/convocatoria_partido.py
"""
Modelo de ConvocatoriaPartido para gestionar las convocatorias de jugadores.
Registra qué jugadores están convocados y cuáles son titulares en cada partido.
"""
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class ConvocatoriaPartido(Base):
    """
    Modelo ORM para la tabla 'convocatoria_partido'.

    Representa la convocatoria de jugadores para un partido específico.
    Un jugador puede estar convocado (va al partido) y dentro de la convocatoria,
    puede ser titular o suplente.

    Attributes:
        id_convocatoria (int): Identificador único (Primary Key)
        id_partido (int): ID del partido (Foreign Key)
        id_jugador (int): ID del jugador (Foreign Key)
        es_titular (bool): Si el jugador es titular (default: False)
        created_at (datetime): Fecha y hora de creación
        partido (Partido): Relación con el partido
        jugador (Jugador): Relación con el jugador
    """
    __tablename__ = "convocatoria_partido"

    # Clave primaria
    id_convocatoria = Column(Integer, primary_key=True, index=True)

    # Relaciones
    id_partido = Column(Integer, ForeignKey("partidos.id_partido", ondelete="CASCADE"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("jugadores.id_jugador", ondelete="CASCADE"), nullable=False)

    # Información de la convocatoria
    es_titular = Column(Boolean, nullable=False, default=False)  # False = suplente

    # Auditoría: fecha de creación
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relaciones ORM
    partido = relationship("Partido", lazy="selectin")
    jugador = relationship("Jugador", lazy="selectin")