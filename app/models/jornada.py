# app/models/jornada.py
"""
Modelo de Jornada para gestionar las fechas de una liga.
Almacena el número de jornada, nombre y fechas de cada jornada.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Jornada(Base):
    """
    Modelo ORM para la tabla 'jornadas'.

    Representa una jornada de una liga, que contiene múltiples partidos.
    Permite organizar el calendario en fechas específicas.

    Attributes:
        id_jornada (int): Identificador único de la jornada (Primary Key)
        id_liga (int): ID de la liga a la que pertenece (Foreign Key)
        numero (int): Número de la jornada (1, 2, 3, etc.)
        nombre (str): Nombre de la jornada (ej: "Jornada 1")
        fecha_inicio (datetime): Fecha de inicio de la jornada
        fecha_fin (datetime): Fecha de fin de la jornada
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "jornadas"

    # Clave primaria
    id_jornada = Column(Integer, primary_key=True)

    # Relaciones
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)

    # Información de la jornada
    numero = Column(Integer, nullable=False)  # Número de jornada (1, 2, 3...)
    nombre = Column(String(50), nullable=False)  # Nombre: "Jornada 1", "Jornada 2", etc.

    # Fechas de la jornada
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)

    # Auditoría
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    liga = relationship("Liga", back_populates="jornadas")
    partidos = relationship("Partido", back_populates="jornada", foreign_keys="Partido.id_jornada")
