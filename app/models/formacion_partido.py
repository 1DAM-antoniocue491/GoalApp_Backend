# app/models/formacion_partido.py
"""
Modelo de Formación utilizada en un Partido específico.
Registra qué formación táctica usó cada equipo en un partido concreto.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from ..database.connection import Base


class FormacionPartido(Base):
    """
    Modelo ORM para la tabla 'formacion_partido'.
    
    Registra la formación táctica que utilizó un equipo en un partido específico.
    Permite analizar qué formaciones se usaron en cada partido.
    
    Attributes:
        id_formacion_partido (int): Identificador único de la relación (Primary Key)
        id_partido (int): ID del partido (Foreign Key)
        id_equipo (int): ID del equipo (Foreign Key)
        id_formacion (int): ID de la formación utilizada (Foreign Key)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "formacion_partido"

    # Clave primaria
    id_formacion_partido = Column(Integer, primary_key=True, index=True)

    # Relaciones: partido, equipo y formación utilizada
    id_partido = Column(Integer, ForeignKey("partidos.id_partido"), nullable=False)
    id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)
    id_formacion = Column(Integer, ForeignKey("formaciones.id_formacion"), nullable=False)

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
