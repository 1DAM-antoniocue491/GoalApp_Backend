# app/models/posicion_formacion.py
"""
Modelo de PosicionFormacion para definir las posiciones del campo de fútbol.
Define las posiciones genéricas que pueden usarse en alineaciones (portero, defensa, etc.).
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database.connection import Base


class PosicionFormacion(Base):
    """
    Modelo ORM para la tabla 'posicion_formacion'.

    Define las posiciones genéricas del campo de fútbol que pueden utilizarse
    en las alineaciones de los partidos. Ejemplos: "Portero", "Defensa Central",
    "Lateral Izquierdo", "Mediocentro", "Extremo Derecho", "Delantero Centro".

    Attributes:
        id_posicion (int): Identificador único de la posición (Primary Key)
        nombre (str): Nombre de la posición (máx. 50 caracteres)
        descripcion (str): Descripción opcional de la posición (máx. 255 caracteres)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "posicion_formacion"

    # Clave primaria
    id_posicion = Column(Integer, primary_key=True)

    # Información de la posición
    nombre = Column(String(50), nullable=False)  # Ejemplo: "Portero", "Defensa Central", "Extremo Derecho"
    descripcion = Column(String(255), nullable=True)  # Descripción opcional

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
