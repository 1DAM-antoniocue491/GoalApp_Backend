"""
Schemas de validación para el recurso FormacionPartido.
Define los modelos Pydantic para request/response de la API relacionados con las formaciones utilizadas por cada equipo en un partido específico.
"""
from pydantic import BaseModel
from datetime import datetime

class FormacionPartidoBase(BaseModel):
    """
    Schema base de FormacionPartido con campos comunes.
    Usado como clase base para herencia. Representa la formación que un equipo usa en un partido determinado.
    
    Attributes:
        id_partido (int): ID del partido
        id_equipo (int): ID del equipo
        id_formacion (int): ID de la formación táctica utilizada en el partido
    """
    id_partido: int
    id_equipo: int
    id_formacion: int

class FormacionPartidoCreate(FormacionPartidoBase):
    """
    Schema para registrar la formación de un equipo en un partido.
    Usado en el endpoint POST /formaciones-partido/
    Hereda todos los campos de FormacionPartidoBase como requeridos.
    """
    pass

class FormacionPartidoUpdate(BaseModel):
    """
    Schema para actualizar la formación de un equipo en un partido.
    Usado en el endpoint PUT/PATCH /formaciones-partido/{id_formacion_partido}
    
    Attributes:
        id_partido (int | None): ID del partido
        id_equipo (int | None): ID del equipo
        id_formacion (int | None): ID de la formación táctica utilizada en el partido
    """
    id_partido: int | None = None
    id_equipo: int | None = None
    id_formacion: int | None = None

class FormacionPartidoResponse(BaseModel):
    """
    Schema de respuesta para la formación de un equipo en un partido.
    Usado en las respuestas de los endpoints GET /formaciones-partido/
    
    Attributes:
        id_formacion_partido (int): Identificador único de la relación formación-partido-equipo
        id_partido (int): ID del partido
        id_equipo (int): ID del equipo
        id_formacion (int): ID de la formación táctica utilizada en el partido
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_formacion_partido: int
    id_partido: int
    id_equipo: int
    id_formacion: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
