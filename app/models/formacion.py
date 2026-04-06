# app/models/formacion.py
"""
Modelo de Formación táctica para definir esquemas de juego.
Define formaciones como 4-4-2, 4-3-3, etc.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database.connection import Base


class Formacion(Base):
    """
    Modelo ORM para la tabla 'formaciones'.
    
    Define las formaciones tácticas disponibles en el sistema.
    Ejemplos: "4-4-2", "4-3-3", "3-5-2", "5-3-2"
    
    Attributes:
        id_formacion (int): Identificador único de la formación (Primary Key)
        nombre (str): Nombre de la formación (ej: "4-4-2", máx. 20 caracteres, único)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "formaciones"

    # Clave primaria
    id_formacion = Column(Integer, primary_key=True, index=True)
    
    # Información de la formación
    nombre = Column(String(20), nullable=False, unique=True)  # Ejemplo: "4-4-2", "4-3-3"

    # Auditoría: fechas de creación y actualización
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
