# app/schemas/invitacion.py
"""
Schemas de validación para el recurso Invitación.
Define los modelos Pydantic para request/response de la API relacionados con invitaciones a ligas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class InvitacionCreate(BaseModel):
    """
    Schema para crear una invitación a una liga.

    Se usa en el endpoint POST /invitaciones/ligas/{liga_id}/invitar donde el admin
    invita a un usuario a unirse a su liga con un rol específico.

    Attributes:
        nombre (str): Nombre completo del usuario invitado
        email (EmailStr): Email del usuario invitado
        id_rol (int): ID del rol a asignar (1=admin, 2=coach, 3=delegate, 4=player, 5=viewer)
        id_equipo (int | None): ID del equipo (nullable para rol viewer)
        dorsal (str | None): Número de dorsal asignado
        posicion (str | None): Posición del jugador
        tipo_jugador (str | None): Tipo de jugador (titular, suplente, etc.)
    """
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    id_rol: int = Field(..., ge=1)
    id_equipo: Optional[int] = Field(None, ge=1)
    dorsal: Optional[str] = Field(None, max_length=10)
    posicion: Optional[str] = Field(None, max_length=50)
    tipo_jugador: Optional[str] = Field(None, max_length=50)


class InvitacionValidarResponse(BaseModel):
    """
    Schema de respuesta para validar una invitación.

    Se usa en el endpoint GET /invitaciones/validar/{token} para que el frontend
    pueda verificar si un token es válido antes de mostrar el formulario de registro.

    Attributes:
        valido (bool): True si el token es válido
        email (str | None): Email del invitado (si es válido)
        nombre (str | None): Nombre completo del invitado (si es válido)
        liga_nombre (str | None): Nombre de la liga (si es válido)
        equipo_nombre (str | None): Nombre del equipo (si es válido)
        rol (str | None): Nombre del rol (si es válido)
        dorsal (str | None): Número de dorsal asignado
        posicion (str | None): Posición del jugador
        tipo_jugador (str | None): Tipo de jugador
        motivo (str | None): Motivo por el que no es válido (si no lo es)
    """
    valido: bool
    email: Optional[str] = None
    nombre: Optional[str] = None
    liga_nombre: Optional[str] = None
    equipo_nombre: Optional[str] = None
    rol: Optional[str] = None
    dorsal: Optional[str] = None
    posicion: Optional[str] = None
    tipo_jugador: Optional[str] = None
    motivo: Optional[str] = None


class InvitacionAceptar(BaseModel):
    """
    Schema para aceptar una invitación y crear usuario.

    Se usa en el endpoint POST /invitaciones/aceptar/{token} donde el usuario
    se registra aceptando la invitación.

    Attributes:
        email (EmailStr): Email del usuario (debe coincidir con la invitación)
        password (str): Contraseña del usuario (mínimo 6 caracteres)
        nombre (str): Nombre del usuario
    """
    email: EmailStr
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., min_length=2, max_length=100)


class InvitacionCodigoCreate(BaseModel):
    """
    Schema para solicitar generación de código de invitación.

    Se usa en el endpoint POST /ligas/{liga_id}/generar-codigo.

    Attributes:
        id_rol (int): ID del rol a asignar (1=admin, 2=coach, 3=delegate, 4=player, 5=viewer)
        id_equipo (int | None): ID del equipo (nullable para rol viewer)
        nombre (str | None): Nombre opcional del invitado
        dorsal (str | None): Número de dorsal asignado
        posicion (str | None): Posición del jugador
        tipo_jugador (str | None): Tipo de jugador (titular, suplente, etc.)
    """
    id_rol: int = Field(..., ge=1)
    id_equipo: Optional[int] = Field(None, ge=1)
    nombre: Optional[str] = Field(None, max_length=100)
    dorsal: Optional[str] = Field(None, max_length=10)
    posicion: Optional[str] = Field(None, max_length=50)
    tipo_jugador: Optional[str] = Field(None, max_length=50)


class InvitacionCodigoResponse(BaseModel):
    """
    Schema de respuesta para código de invitación generado.

    Attributes:
        codigo (str): Código corto alfanumérico (6-8 caracteres)
        rol (str): Nombre del rol asignado
        liga (str): Nombre de la liga
        expiracion (datetime): Fecha de expiración del código
        id_equipo (int | None): ID del equipo (si aplica)
    """
    codigo: str
    rol: str
    liga: str
    expiracion: datetime
    id_equipo: Optional[int] = None


class InvitacionAceptarCodigo(BaseModel):
    """
    Schema para aceptar invitación mediante código corto.

    Se usa en el endpoint POST /invitaciones/aceptar-codigo/{codigo}.

    Attributes:
        email (EmailStr): Email del usuario
        password (str): Contraseña del usuario (mínimo 6 caracteres)
        nombre (str): Nombre del usuario
    """
    email: EmailStr
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., min_length=2, max_length=100)
