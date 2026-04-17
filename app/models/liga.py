# app/models/liga.py
"""
Modelo de Liga para gestionar competiciones.
Representa una liga o torneo con sus equipos y partidos.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Liga(Base):
    """
    Modelo ORM para la tabla 'ligas'.

    Una liga agrupa equipos y partidos de una misma competición y temporada.
    Ejemplo: "Liga Amateur Madrid 2024/2025"

    Attributes:
        id_liga (int): Identificador único de la liga (Primary Key)
        nombre (str): Nombre de la liga (máx. 100 caracteres, único)
        temporada (str): Temporada de la liga (ej: "2024/2025", máx. 20 caracteres)
        activa (bool): Si la liga está activa (default: True)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        equipos (list): Lista de equipos en la liga (relación 1:N)
        configuracion (LigaConfiguracion): Configuración de la liga (relación 1:1)
    """
    __tablename__ = "ligas"

    # Clave primaria
    id_liga = Column(Integer, primary_key=True)

    # Información de la liga
    nombre = Column(String(100), nullable=False, unique=True)  # Nombre único de la liga
    temporada = Column(String(20), nullable=False)  # Ejemplo: "2024/2025"
    categoria = Column(String(50), nullable=True)  # Senior, Juvenil A, Cadete, etc.
    activa = Column(Boolean, nullable=False, default=True)  # Liga activa/inactiva

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    equipos = relationship("Equipo", back_populates="liga", lazy="raise")
    configuracion = relationship("LigaConfiguracion", back_populates="liga", uselist=False, lazy="raise")
    usuario_roles = relationship("UsuarioRol", back_populates="liga", lazy="raise")
