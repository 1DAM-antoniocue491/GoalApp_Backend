# app/models/alineacion_partido.py
"""
Modelo de AlineacionPartido para gestionar las alineaciones de jugadores en partidos.
Define qué jugador ocupa qué posición en un partido específico.
"""
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class AlineacionPartido(Base):
    """
    Modelo ORM para la tabla 'alineacion_partido'.

    Representa la alineación de jugadores en un partido específico,
    indicando qué jugador es titular o suplente.

    Attributes:
        id_alineacion (int): Identificador único (Primary Key)
        id_partido (int): ID del partido (Foreign Key)
        id_jugador (int): ID del jugador (Foreign Key)
        id_posicion (str): Posición en el campo ("portero", "defensa", "mediocentro", "centrocampista", "delantero")
        titular (bool): Si el jugador es titular (default: False)
        created_at (datetime): Fecha y hora de creación
        updated_at (datetime): Fecha y hora de última actualización
        partido (Partido): Relación con el partido
        jugador (Jugador): Relación con el jugador
    """
    __tablename__ = "alineacion_partido"

    # Clave primaria
    id_alineacion = Column(Integer, primary_key=True)

    # Relaciones
    id_partido = Column(Integer, ForeignKey("partidos.id_partido", ondelete="CASCADE"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("jugadores.id_jugador", ondelete="CASCADE"), nullable=False)
    id_posicion = Column(String(50), nullable=False)  # Posición en el campo: "portero", "defensa", "mediocentro", "centrocampista", "delantero"

    # Información de la alineación
    titular = Column(Boolean, nullable=False, default=False)  # False = suplente

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    partido = relationship("Partido", back_populates="alineaciones", lazy="raise")
    jugador = relationship("Jugador", lazy="raise")