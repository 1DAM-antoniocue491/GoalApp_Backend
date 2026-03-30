"""
Schemas de validación para el recurso Formacion.
Define los modelos Pydantic para request/response de la API relacionados con formaciones tácticas.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class FormacionBase(BaseModel):
    """
    Schema base de Formacion con campos comunes.
    Usado como clase base para herencia.
    
    Attributes:
        nombre (str): Nombre de la formación táctica (ej: 4-4-2, 4-3-3, máximo 20 caracteres)
    """
    nombre: str = Field(..., max_length=20)

class FormacionCreate(FormacionBase):
    """
    Schema para crear una nueva formación táctica.
    Usado en el endpoint POST /formaciones/
    Hereda todos los campos de FormacionBase como requeridos.
    """
    pass

class FormacionUpdate(BaseModel):
    """
    Schema para actualizar una formación táctica existente.
    Usado en el endpoint PUT/PATCH /formaciones/{id_formacion}
    
    Attributes:
        nombre (str | None): Nombre de la formación táctica (ej: 4-4-2, 4-3-3, máximo 20 caracteres)
    """
    nombre: str | None = Field(None, max_length=20)

class FormacionResponse(BaseModel):
    """
    Schema de respuesta para una formación táctica.
    Usado en las respuestas de los endpoints GET /formaciones/
    
    Attributes:
        id_formacion (int): Identificador único de la formación
        nombre (str): Nombre de la formación táctica (ej: 4-4-2, 4-3-3)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_formacion: int
    nombre: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
