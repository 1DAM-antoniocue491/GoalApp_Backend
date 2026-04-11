# app/schemas/token_recuperacion.py
"""
Schemas de TokenRecuperacion para la gestión administrativa de tokens.
Define los modelos Pydantic para consultar y gestionar tokens de recuperación.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TokenRecuperacionBase(BaseModel):
    """
    Schema base para token de recuperación.

    Attributes:
        id_usuario (int): ID del usuario propietario del token
    """
    id_usuario: int = Field(..., description="ID del usuario")


class TokenRecuperacionResponse(BaseModel):
    """
    Schema de respuesta para un token de recuperación.

    Attributes:
        id_token (int): ID del token
        id_usuario (int): ID del usuario
        token (str): Token de recuperación (parcialmente oculto por seguridad)
        fecha_expiracion (datetime): Fecha de expiración
        usado (bool): Si el token ya fue usado
        created_at (datetime): Fecha de creación
    """
    id_token: int
    id_usuario: int
    token: str
    fecha_expiracion: datetime
    usado: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenDetalladoResponse(BaseModel):
    """
    Schema de respuesta detallada para un token con información del usuario.

    Attributes:
        id_token (int): ID del token
        id_usuario (int): ID del usuario
        nombre_usuario (str): Nombre del usuario
        email_usuario (str): Email del usuario
        token (str): Token de recuperación (parcialmente oculto)
        fecha_expiracion (datetime): Fecha de expiración
        usado (bool): Si el token ya fue usado
        created_at (datetime): Fecha de creación
    """
    id_token: int
    id_usuario: int
    nombre_usuario: str
    email_usuario: str
    token: str
    fecha_expiracion: datetime
    usado: bool
    created_at: datetime


class TokenEstadisticasResponse(BaseModel):
    """
    Schema de respuesta para estadísticas de tokens.

    Attributes:
        total (int): Total de tokens
        activos (int): Tokens activos (no usados y no expirados)
        usados (int): Tokens usados
        expirados (int): Tokens expirados sin usar
    """
    total: int
    activos: int
    usados: int
    expirados: int