# app/models/jugador.py
"""
Modelo de Jugador para vincular usuarios con equipos.
Almacena información deportiva del jugador (posición, dorsal, estado).
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Jugador(Base):
    """
    Modelo ORM para la tabla 'jugadores'.

    Vincula un usuario con un equipo como jugador, añadiendo información
    deportiva específica (posición, dorsal, estado activo/inactivo).

    Attributes:
        id_jugador (int): Identificador único del jugador (Primary Key)
        id_usuario (int): ID del usuario asociado (Foreign Key, único)
        id_equipo (int): ID del equipo al que pertenece (Foreign Key)
        posicion (str): Posición en el campo (ej: "Delantero", máx. 50 caracteres)
        dorsal (int): Número de dorsal del jugador
        activo (bool): Si el jugador está activo en el equipo (default: True)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        usuario (Usuario): Relación con el usuario
        equipo (Equipo): Relación con el equipo
    """
    __tablename__ = "jugadores"

    # Clave primaria
    id_jugador = Column(Integer, primary_key=True)

    # Relaciones: usuario y equipo
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False, unique=True)  # Un usuario = un jugador
    id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)

    # Información deportiva
    posicion = Column(String(50), nullable=False)  # Ejemplo: "Portero", "Defensa", "Centrocampista", "Delantero"
    dorsal = Column(Integer, nullable=False)  # Número de camiseta
    activo = Column(Boolean, nullable=False, default=True)  # Si está activo en el equipo

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    usuario = relationship("Usuario", lazy="raise")
    equipo = relationship("Equipo", back_populates="jugadores", lazy="raise")
