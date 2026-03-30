"""
Schemas de validación para el recurso PosicionFormacion.
Define los modelos Pydantic para request/response de la API relacionados con las posiciones específicas dentro de una formación táctica.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class PosicionFormacionBase(BaseModel):
    """
    Schema base de PosicionFormacion con campos comunes.
    Usado como clase base para herencia. Define las posiciones específicas dentro de una formación.
    
    Attributes:
        id_formacion (int): ID de la formación táctica a la que pertenece esta posición
        nombre (str): Nombre de la posición (ej: portero, defensa central izquierdo, delantero centro, máximo 50 caracteres)
    """
    id_formacion: int
    nombre: str = Field(..., max_length=50)

class PosicionFormacionCreate(PosicionFormacionBase):
    """
    Schema para crear una nueva posición dentro de una formación.
    Usado en el endpoint POST /posiciones-formacion/
    Hereda todos los campos de PosicionFormacionBase como requeridos.
    """
    pass

class PosicionFormacionUpdate(BaseModel):
    """
    Schema para actualizar una posición de formación existente.
    Usado en el endpoint PUT/PATCH /posiciones-formacion/{id_posicion}
    
    Attributes:
        id_formacion (int | None): ID de la formación táctica a la que pertenece esta posición
        nombre (str | None): Nombre de la posición (máximo 50 caracteres)
    """
    id_formacion: int | None = None
    nombre: str | None = Field(None, max_length=50)

class PosicionFormacionResponse(BaseModel):
    """
    Schema de respuesta para una posición de formación.
    Usado en las respuestas de los endpoints GET /posiciones-formacion/
    
    Attributes:
        id_posicion (int): Identificador único de la posición
        id_formacion (int): ID de la formación táctica a la que pertenece esta posición
        nombre (str): Nombre de la posición
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_posicion: int
    id_formacion: int
    nombre: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
