"""
Schemas de validación para el recurso PosicionFormacion.
Define los modelos Pydantic para request/response de la API relacionados con las posiciones genéricas del campo.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PosicionFormacionBase(BaseModel):
    """
    Schema base de PosicionFormacion con campos comunes.
    Define las posiciones genéricas del campo de fútbol.

    Attributes:
        nombre (str): Nombre de la posición (ej: Portero, Defensa Central, Extremo Derecho, máximo 50 caracteres)
        descripcion (str | None): Descripción opcional de la posición (máximo 255 caracteres)
    """
    nombre: str = Field(..., max_length=50, description="Nombre de la posición")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción opcional de la posición")


class PosicionFormacionCreate(PosicionFormacionBase):
    """
    Schema para crear una nueva posición de formación.
    Usado en el endpoint POST /posiciones-formacion/
    Hereda todos los campos de PosicionFormacionBase.
    """
    pass


class PosicionFormacionUpdate(BaseModel):
    """
    Schema para actualizar una posición de formación existente.
    Usado en el endpoint PUT/PATCH /posiciones-formacion/{id_posicion}

    Attributes:
        nombre (str | None): Nombre de la posición (máximo 50 caracteres)
        descripcion (str | None): Descripción opcional (máximo 255 caracteres)
    """
    nombre: Optional[str] = Field(None, max_length=50, description="Nombre de la posición")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción opcional")


class PosicionFormacionResponse(BaseModel):
    """
    Schema de respuesta para una posición de formación.
    Usado en las respuestas de los endpoints GET /posiciones-formacion/

    Attributes:
        id_posicion (int): Identificador único de la posición
        nombre (str): Nombre de la posición
        descripcion (str | None): Descripción de la posición
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_posicion: int
    nombre: str
    descripcion: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
