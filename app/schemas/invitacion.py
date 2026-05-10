# app/schemas/invitacion.py
"""
Schemas de validación para el recurso Invitación.
Define los modelos Pydantic para request/response de la API relacionados con invitaciones a ligas.
"""
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from datetime import datetime


PLAYER_ROLE_ID = 4  # init.sql: 1=admin, 2=coach, 3=delegate, 4=player, 5=viewer


def _validar_campos_jugador(id_rol: int, id_equipo: int | None, dorsal: str | None, posicion: str | None) -> None:
    """
    Valida los campos mínimos para invitar a un jugador.

    La tabla `jugadores` tiene `dorsal INT NOT NULL` y `posicion NOT NULL`, por eso
    estos datos deben bloquearse ya en el schema cuando `id_rol == 4`.
    """
    if id_rol != PLAYER_ROLE_ID:
        return

    if id_equipo is None:
        raise ValueError("El equipo es obligatorio cuando el rol invitado es jugador")

    dorsal_limpio = str(dorsal).strip() if dorsal is not None else ""
    if not dorsal_limpio:
        raise ValueError("El dorsal es obligatorio cuando el rol invitado es jugador")

    try:
        dorsal_int = int(dorsal_limpio)
    except ValueError:
        raise ValueError("El dorsal debe ser un número entero")

    if dorsal_int < 0:
        raise ValueError("El dorsal no puede ser negativo")

    if not (posicion or "").strip():
        raise ValueError("La posición es obligatoria cuando el rol invitado es jugador")


class InvitacionCreate(BaseModel):
    """
    Schema para crear una invitación a una liga.

    Se usa en el endpoint POST /invitaciones/ligas/{liga_id}/invitar donde el admin
    o entrenador autorizado invita a un usuario con un rol específico.
    """
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    id_rol: int = Field(..., ge=1)
    id_equipo: Optional[int] = Field(None, ge=1)
    dorsal: Optional[str] = Field(None, max_length=10)
    posicion: Optional[str] = Field(None, max_length=50)
    tipo_jugador: Optional[str] = Field(None, max_length=50)

    @model_validator(mode="after")
    def validar_datos_deportivos_si_es_jugador(self):
        """Evita crear invitaciones player incompletas que luego fallarían al aceptar."""
        _validar_campos_jugador(self.id_rol, self.id_equipo, self.dorsal, self.posicion)
        return self


class InvitacionValidarResponse(BaseModel):
    """Schema de respuesta para validar una invitación antes de aceptarla."""
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
    """Schema para aceptar una invitación por token y crear usuario si hace falta."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., min_length=2, max_length=100)


class InvitacionCodigoCreate(BaseModel):
    """Schema para solicitar generación de código de invitación."""
    id_rol: int = Field(..., ge=1)
    id_equipo: Optional[int] = Field(None, ge=1)
    nombre: Optional[str] = Field(None, max_length=100)
    dorsal: Optional[str] = Field(None, max_length=10)
    posicion: Optional[str] = Field(None, max_length=50)
    tipo_jugador: Optional[str] = Field(None, max_length=50)

    @model_validator(mode="after")
    def validar_datos_deportivos_si_es_jugador(self):
        """El código también necesita datos deportivos completos si invita a player."""
        _validar_campos_jugador(self.id_rol, self.id_equipo, self.dorsal, self.posicion)
        return self


class InvitacionCodigoResponse(BaseModel):
    """Schema de respuesta para código de invitación generado."""
    codigo: str
    rol: str
    liga: str
    expiracion: datetime
    id_equipo: Optional[int] = None


class InvitacionAceptarCodigo(BaseModel):
    """
    Schema para aceptar invitación mediante código corto.

    Si el usuario ya está autenticado, el router puede usar current_user y estos
    campos pueden omitirse. Si no, email, password y nombre son necesarios.
    """
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
