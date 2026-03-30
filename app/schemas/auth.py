# app/schemas/auth.py
"""
Schemas de autenticación para validación de requests y responses.
Gestiona los esquemas para el flujo de recuperación de contraseña.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class PasswordResetRequest(BaseModel):
    """
    Schema para solicitar recuperación de contraseña.

    Se usa en el endpoint POST /auth/forgot-password donde el usuario
    proporciona su email para iniciar el proceso de recuperación.

    Attributes:
        email (EmailStr): Email del usuario que solicita recuperación
    """
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """
    Schema para confirmar recuperación de contraseña.

    Se usa en el endpoint POST /auth/reset-password donde el usuario
    proporciona el token recibido por email y su nueva contraseña.

    Attributes:
        token (str): Token de recuperación recibido por email
        nueva_contrasena (str): Nueva contraseña del usuario (mínimo 6 caracteres)
    """
    token: str
    nueva_contrasena: str


class PasswordResetResponse(BaseModel):
    """
    Schema de respuesta para operaciones de recuperación.

    Attributes:
        mensaje (str): Mensaje informativo sobre el resultado de la operación
    """
    mensaje: str