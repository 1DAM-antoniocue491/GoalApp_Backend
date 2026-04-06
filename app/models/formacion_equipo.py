# app/models/formacion_equipo.py
"""
Modelo de relación Formación-Equipo.
Vincula un equipo con su formación táctica preferida.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..database.connection import Base


class FormacionEquipo(Base):
    """
    Modelo ORM para la tabla 'formacion_equipo'.
    
    Tabla intermedia que vincula un equipo con su formación táctica predeterminada.
    Un equipo puede tener una formación preferida que usa generalmente.
    
    Attributes:
        id_formacion_equipo (int): Identificador único de la relación (Primary Key)
        id_equipo (int): ID del equipo (Foreign Key)
        id_formacion (int): ID de la formación táctica (Foreign Key)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "formacion_equipo"

    # Clave primaria
    id_formacion_equipo = Column(Integer, primary_key=True, index=True)

    # Relaciones: equipo y formación
    id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)
    id_formacion = Column(Integer, ForeignKey("formaciones.id_formacion"), nullable=False)

    # Auditoría: fechas de creación y actualización
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
