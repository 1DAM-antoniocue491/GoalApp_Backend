"""
Schemas de validación para el recurso Usuario.
Define los modelos Pydantic para request/response de la API relacionados con usuarios del sistema.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, date
from enum import Enum
import re


class GeneroEnum(str, Enum):
    """Enumeración para el género del usuario."""
    masculino = "masculino"
    femenino = "femenino"
    otro = "otro"


class UsuarioBase(BaseModel):
    """
    Schema base de Usuario con campos comunes.
    Usado como clase base para herencia.

    Attributes:
        nombre (str): Nombre completo del usuario (máximo 100 caracteres)
        email (EmailStr): Correo electrónico válido del usuario
    """
    nombre: str = Field(..., max_length=100)
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    """
    Schema para crear un nuevo usuario.
    Usado en el endpoint POST /usuarios/

    NOTA: El registro solo requiere nombre, email y contraseña.
    Los campos adicionales (género, teléfono, fecha_nacimiento) se
    añaden posteriormente desde el perfil del usuario.

    Attributes:
        nombre (str): Nombre completo del usuario (máximo 100 caracteres)
        email (EmailStr): Correo electrónico válido del usuario
        password (str): Contraseña en texto plano (mínimo 6 caracteres, se hasheará en el servidor)
    """
    password: str = Field(
        ...,
        min_length=6,
        alias="contraseña",
    )
    @field_validator("password")
    def validar_longitud_maxima(cls, v: str) -> str:
        """
        bcrypt solo permite contraseñas de **≤ 72 bytes**.
        Este método verifica que la cadena codificada en UTF‑8 no supere
        ese límite.
        """
        max_bytes = 72
        if len(v.encode("utf-8")) > max_bytes:
            raise ValueError(
                f"La contraseña no puede superar los {max_bytes} bytes "
                "(≈ 72 caracteres ASCII)."
            )
        return v

    class Config:
        validate_by_name = True

class UsuarioUpdate(BaseModel):
    """
    Schema para actualizar un usuario existente.
    Usado en el endpoint PUT/PATCH /usuarios/{id_usuario}

    Todos los campos son opcionales para permitir actualizaciones parciales.
    El usuario puede completar su perfil con género, teléfono y fecha de nacimiento.

    Attributes:
        nombre (str | None): Nombre completo del usuario (máximo 100 caracteres)
        email (EmailStr | None): Correo electrónico válido del usuario
        contraseña (str | None): Nueva contraseña (mínimo 6 caracteres)
        genero (GeneroEnum | None): Género del usuario
        telefono (str | None): Número de teléfono (máximo 20 caracteres)
        fecha_nacimiento (date | None): Fecha de nacimiento
        imagen_url (str | None): URL de la imagen de perfil
    """
    nombre: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    contraseña: str | None = Field(None, min_length=6)
    genero: GeneroEnum | None = None
    telefono: str | None = Field(None, max_length=20)
    fecha_nacimiento: date | None = None
    imagen_url: str | None = Field(None, max_length=255)

    @field_validator("telefono")
    def validar_telefono(cls, v: str | None) -> str | None:
        """
        Valida el formato del teléfono.
        Acepta formatos: +34612345678, 612345678, +34 612 345 678
        """
        if v is None:
            return v
        # Eliminar espacios y guiones
        telefono_limpio = re.sub(r"[\s\-]", "", v)
        # Validar formato: puede empezar con + seguido de código país, luego 9 dígitos
        patron = r"^(\+\d{1,3})?\d{6,14}$"
        if not re.match(patron, telefono_limpio):
            raise ValueError("Formato de teléfono inválido")
        return telefono_limpio

class UsuarioResponse(BaseModel):
    """
    Schema de respuesta para un usuario.
    Usado en las respuestas de los endpoints GET /usuarios/

    Attributes:
        id_usuario (int): Identificador único del usuario
        nombre (str): Nombre completo del usuario
        email (EmailStr): Correo electrónico del usuario
        genero (GeneroEnum | None): Género del usuario
        telefono (str | None): Número de teléfono
        fecha_nacimiento (date | None): Fecha de nacimiento
        imagen_url (str | None): URL de la imagen de perfil
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    id_usuario: int
    nombre: str
    email: EmailStr
    genero: GeneroEnum | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None
    imagen_url: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LigaConRolResponse(BaseModel):
    """
    Schema de respuesta para una liga donde el usuario tiene un rol asignado.

    Incluye informacion basica de la liga y el rol del usuario en ella.

    Attributes:
        id_liga (int): ID de la liga
        nombre (str): Nombre de la liga
        temporada (str): Temporada de la liga
        activa (bool): Si la liga esta activa
        rol (str): Nombre del rol del usuario en esta liga
        equipos_total (int): Cantidad de equipos inscritos en la liga
    """
    id_liga: int
    nombre: str
    temporada: str
    activa: bool
    rol: str
    equipos_total: int = 0

    class Config:
        from_attributes = True


class UsuarioConRolEnLigaResponse(BaseModel):
    """
    Schema de respuesta para un usuario con su rol en una liga específica.

    Incluye información del usuario y el rol que tiene en una liga.

    Attributes:
        id_usuario (int): ID del usuario
        nombre (str): Nombre completo del usuario
        email (EmailStr): Correo electrónico del usuario
        id_rol (int): ID del rol en esta liga
        rol (str): Nombre del rol (admin, entrenador, delegado, jugador, etc.)
        activo (bool): Si el usuario está activo en la liga
    """
    id_usuario: int
    nombre: str
    email: EmailStr
    id_rol: int
    rol: str
    activo: bool

    class Config:
        from_attributes = True
