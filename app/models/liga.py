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
        nombre (str): Nombre de la liga (máx. 100 caracteres)
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
    nombre = Column(String(100), nullable=False)  # Nombre de la liga (no único, puede repetirse entre usuarios)
    temporada = Column(String(20), nullable=False)  # Ejemplo: "2024/2025"
    categoria = Column(String(50), nullable=True)  # Senior, Juvenil A, Cadete, etc.
    activa = Column(Boolean, nullable=False, default=True)  # Liga activa/inactiva

    # Configuración adicional de la liga
    cantidad_partidos = Column(Integer, nullable=True)  # Número máximo de partidos por equipo
    duracion_partido = Column(Integer, nullable=True)  # Duración en minutos
    logo_url = Column(Text, nullable=True)  # URL o base64 del logo de la liga

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    # cascade="all, delete-orphan" asegura que al eliminar la liga se eliminen todos los dependientes
    equipos = relationship("Equipo", back_populates="liga", lazy="raise", cascade="all, delete-orphan")
    configuracion = relationship("LigaConfiguracion", back_populates="liga", uselist=False, lazy="raise", cascade="all, delete-orphan")
    usuario_roles = relationship("UsuarioRol", back_populates="liga", lazy="raise", cascade="all, delete-orphan")
    jornadas = relationship("Jornada", back_populates="liga", lazy="raise", cascade="all, delete-orphan")
    invitaciones = relationship("Invitacion", back_populates="liga", lazy="raise", cascade="all, delete-orphan")
    seguidores = relationship("UsuarioSigueLiga", back_populates="liga", lazy="raise", cascade="all, delete-orphan")
    partidos = relationship("Partido", back_populates="liga", lazy="raise", cascade="all, delete-orphan")
