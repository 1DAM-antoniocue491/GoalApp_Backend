# app/models/equipo.py
"""
Modelo de Equipo para gestionar los equipos de la liga.
Incluye información del equipo, entrenador y delegado.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Equipo(Base):
    """
    Modelo ORM para la tabla 'equipos'.

    Representa un equipo participante en una liga con su información básica,
    pertenencia a una liga, y referencias a su entrenador y delegado.

    Attributes:
        id_equipo (int): Identificador único del equipo (Primary Key)
        nombre (str): Nombre del equipo (máx. 100 caracteres, único)
        ciudad (str): Ciudad del equipo (opcional, máx. 255 caracteres)
        escudo (str): URL o path del escudo del equipo (opcional, máx. 255 caracteres)
        colores (str): Colores del equipo (opcional, máx. 50 caracteres)
        id_liga (int): ID de la liga a la que pertenece (Foreign Key)
        id_entrenador (int | None): ID del usuario que es entrenador (Foreign Key, opcional)
        id_delegado (int | None): ID del usuario que es delegado (Foreign Key, opcional)
        estadio (str): Nombre del estadio del equipo (opcional, máx. 255 caracteres)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        liga (Liga): Relación con la liga
        entrenador (Usuario | None): Relación con el usuario entrenador
        delegado (Usuario | None): Relación con el usuario delegado
    """
    __tablename__ = "equipos"

    # Clave primaria
    id_equipo = Column(Integer, primary_key=True)

    # Información básica del equipo
    nombre = Column(String(100), nullable=False, unique=True)  # Nombre único del equipo
    ciudad = Column(String(255), nullable=True)  # Ciudad del equipo (opcional)
    escudo = Column(String(255), nullable=True)  # URL o path del escudo (opcional)
    colores = Column(String(50), nullable=True)  # Ejemplo: "Azul y Blanco"

    # Relaciones: liga, entrenador y delegado
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)
    id_entrenador = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    id_delegado = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    estadio = Column(String(255), nullable=True)  # Nombre del estadio (opcional)

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    # cascade="all, delete-orphan" asegura que al eliminar el equipo se eliminen sus dependientes
    liga = relationship("Liga", back_populates="equipos", lazy="raise")
    entrenador = relationship("Usuario", foreign_keys=[id_entrenador], lazy="raise")
    delegado = relationship("Usuario", foreign_keys=[id_delegado], lazy="raise")
    jugadores = relationship("Jugador", back_populates="equipo", lazy="raise", cascade="all, delete-orphan")
    formaciones_equipo = relationship("FormacionEquipo", back_populates="equipo", lazy="raise", cascade="all, delete-orphan")
    formaciones_partido = relationship("FormacionPartido", back_populates="equipo", lazy="raise", cascade="all, delete-orphan")
    partidos_local = relationship("Partido", foreign_keys="Partido.id_equipo_local", lazy="raise", cascade="all, delete-orphan")
    partidos_visitante = relationship("Partido", foreign_keys="Partido.id_equipo_visitante", lazy="raise", cascade="all, delete-orphan")
    invitaciones = relationship("Invitacion", back_populates="equipo", lazy="raise", cascade="all, delete-orphan")
