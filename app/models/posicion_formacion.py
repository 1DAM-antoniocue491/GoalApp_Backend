# app/models/posicion_formacion.py
"""
Modelo de Posición en Formación para definir roles en el esquema táctico.
Define las posiciones específicas dentro de una formación.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from ..database.connection import Base


class PosicionFormacion(Base):
    """
    Modelo ORM para la tabla 'posiciones_formacion'.
    
    Define las posiciones específicas dentro de una formación táctica.
    Por ejemplo, en un 4-4-2: "Defensa Central Izquierdo", "Lateral Derecho", etc.
    
    Attributes:
        id_posicion (int): Identificador único de la posición (Primary Key)
        id_formacion (int): ID de la formación a la que pertenece (Foreign Key)
        nombre (str): Nombre de la posición específica (máx. 50 caracteres)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "posiciones_formacion"

    # Clave primaria
    id_posicion = Column(Integer, primary_key=True, index=True)
    
    # Relación: formación a la que pertenece
    id_formacion = Column(Integer, ForeignKey("formaciones.id_formacion"), nullable=False)

    # Información de la posición
    nombre = Column(String(50), nullable=False)  # Ejemplo: "Defensa Central Izquierdo", "Extremo Derecho"

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
