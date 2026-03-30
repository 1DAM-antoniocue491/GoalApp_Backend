"""
Schemas de validación para el recurso Rol.
Define los modelos Pydantic para request/response de la API relacionados con roles de usuario en el sistema.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class RolBase(BaseModel):
    """
    Schema base de Rol con campos comunes.
    Usado como clase base para herencia. Define los roles que pueden tener los usuarios (ej: admin, jugador, entrenador, delegado).
    
    Attributes:
        nombre (str): Nombre del rol (máximo 50 caracteres)
        descripcion (str | None): Descripción opcional del rol (máximo 255 caracteres)
    """
    nombre: str = Field(..., max_length=50)
    descripcion: str | None = Field(None, max_length=255)

class RolCreate(RolBase):
    """
    Schema para crear un nuevo rol.
    Usado en el endpoint POST /roles/
    Hereda todos los campos de RolBase como requeridos.
    """
    pass

class RolUpdate(BaseModel):
    """
    Schema para actualizar un rol existente.
    Usado en el endpoint PUT/PATCH /roles/{id_rol}
    
    Attributes:
        nombre (str | None): Nombre del rol (máximo 50 caracteres)
        descripcion (str | None): Descripción opcional del rol (máximo 255 caracteres)
    """
    nombre: str | None = Field(None, max_length=50)
    descripcion: str | None = Field(None, max_length=255)

class RolResponse(BaseModel):
    """
    Schema de respuesta para un rol.
    Usado en las respuestas de los endpoints GET /roles/
    
    Attributes:
        id_rol (int): Identificador único del rol
        nombre (str): Nombre del rol
        descripcion (str | None): Descripción opcional del rol
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_rol: int
    nombre: str
    descripcion: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
