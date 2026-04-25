"""
Schemas para la gestión de usuarios de liga.
Define los modelos Pydantic para actualizar roles, estados y eliminar usuarios.
"""
from pydantic import BaseModel, Field
from typing import Optional


class UsuarioRolUpdate(BaseModel):
    """
    Schema para actualizar el rol de un usuario en una liga.

    Attributes:
        id_rol (int): Nuevo ID del rol a asignar
    """
    id_rol: int = Field(..., description="ID del nuevo rol a asignar")


class UsuarioEstadoUpdate(BaseModel):
    """
    Schema para actualizar el estado de un usuario en una liga.

    Attributes:
        activo (bool): Nuevo estado (True=activo, False=pendiente)
    """
    activo: bool = Field(..., description="Estado del usuario (True=activo, False=pendiente)")


class UsuarioLigaResponse(BaseModel):
    """
    Schema de respuesta para información de usuario en liga.

    Attributes:
        id_usuario_rol (int): ID de la asignación usuario-rol
        id_usuario (int): ID del usuario
        nombre_usuario (str): Nombre del usuario
        email (str): Email del usuario
        id_rol (int): ID del rol actual
        nombre_rol (str): Nombre del rol actual
        activo (bool): Estado del usuario (True=activo, False=pendiente)
    """
    id_usuario_rol: int
    id_usuario: int
    nombre_usuario: str
    email: str
    id_rol: int
    nombre_rol: str
    activo: bool

    class Config:
        from_attributes = True
