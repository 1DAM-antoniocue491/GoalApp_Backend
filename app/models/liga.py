# app/models/liga.py
"""
Modelo de Liga para gestionar competiciones.
Representa una liga o torneo con sus equipos y partidos.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
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
    id_liga = Column(Integer, primary_key=True, index=True)

    # Información de la liga
    nombre = Column(String(100), nullable=False, unique=True)  # Nombre único de la liga
    temporada = Column(String(20), nullable=False)  # Ejemplo: "2024/2025"
    activa = Column(Boolean, nullable=False, default=True)  # Liga activa/inactiva

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'), nullable=False)

    # Relaciones
    equipos = relationship("Equipo", back_populates="liga", lazy="selectin")
    configuracion = relationship("LigaConfiguracion", back_populates="liga", uselist=False, lazy="selectin")
