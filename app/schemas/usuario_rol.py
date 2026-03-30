"""
Schemas de validación para el recurso UsuarioRol.
Define los modelos Pydantic para request/response de la API relacionados con la asignación de roles a usuarios.
"""
from pydantic import BaseModel
from datetime import datetime

class UsuarioRolBase(BaseModel):
    """
    Schema base de UsuarioRol con campos comunes.
    Usado como clase base para herencia. Representa la relación muchos-a-muchos entre usuarios y roles.
    
    Attributes:
        id_usuario (int): ID del usuario
        id_rol (int): ID del rol asignado al usuario
    """
    id_usuario: int
    id_rol: int

class UsuarioRolCreate(UsuarioRolBase):
    """
    Schema para asignar un rol a un usuario.
    Usado en el endpoint POST /usuarios-roles/
    Hereda todos los campos de UsuarioRolBase como requeridos.
    """
    pass

class UsuarioRolUpdate(BaseModel):
    """
    Schema para actualizar la asignación de rol a un usuario.
    Usado en el endpoint PUT/PATCH /usuarios-roles/{id_usuario_rol}
    
    Attributes:
        id_usuario (int | None): ID del usuario
        id_rol (int | None): ID del rol asignado al usuario
    """
    id_usuario: int | None = None
    id_rol: int | None = None

class UsuarioRolResponse(BaseModel):
    """
    Schema de respuesta para la asignación de rol a un usuario.
    Usado en las respuestas de los endpoints GET /usuarios-roles/
    
    Attributes:
        id_usuario_rol (int): Identificador único de la relación usuario-rol
        id_usuario (int): ID del usuario
        id_rol (int): ID del rol asignado al usuario
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_usuario_rol: int
    id_usuario: int
    id_rol: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
