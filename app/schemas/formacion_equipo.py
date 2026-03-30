"""
Schemas de validación para el recurso FormacionEquipo.
Define los modelos Pydantic para request/response de la API relacionados con las formaciones predeterminadas de cada equipo.
"""
from pydantic import BaseModel
from datetime import datetime

class FormacionEquipoBase(BaseModel):
    """
    Schema base de FormacionEquipo con campos comunes.
    Usado como clase base para herencia. Representa la relación entre equipos y sus formaciones preferidas.
    
    Attributes:
        id_equipo (int): ID del equipo
        id_formacion (int): ID de la formación táctica que utiliza el equipo
    """
    id_equipo: int
    id_formacion: int

class FormacionEquipoCreate(FormacionEquipoBase):
    """
    Schema para asignar una formación a un equipo.
    Usado en el endpoint POST /formaciones-equipo/
    Hereda todos los campos de FormacionEquipoBase como requeridos.
    """
    pass

class FormacionEquipoUpdate(BaseModel):
    """
    Schema para actualizar la formación de un equipo.
    Usado en el endpoint PUT/PATCH /formaciones-equipo/{id_formacion_equipo}
    
    Attributes:
        id_equipo (int | None): ID del equipo
        id_formacion (int | None): ID de la formación táctica que utiliza el equipo
    """
    id_equipo: int | None = None
    id_formacion: int | None = None

class FormacionEquipoResponse(BaseModel):
    """
    Schema de respuesta para la formación de un equipo.
    Usado en las respuestas de los endpoints GET /formaciones-equipo/
    
    Attributes:
        id_formacion_equipo (int): Identificador único de la relación formación-equipo
        id_equipo (int): ID del equipo
        id_formacion (int): ID de la formación táctica que utiliza el equipo
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_formacion_equipo: int
    id_equipo: int
    id_formacion: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
