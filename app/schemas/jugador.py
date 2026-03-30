"""
Schemas de validación para el recurso Jugador.
Define los modelos Pydantic para request/response de la API relacionados con jugadores de fútbol.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class JugadorBase(BaseModel):
    """
    Schema base de Jugador con campos comunes.
    Usado como clase base para herencia.
    
    Attributes:
        id_usuario (int): ID del usuario asociado al jugador
        id_equipo (int): ID del equipo al que pertenece el jugador
        posicion (str): Posición del jugador en el campo (ej: portero, defensa, centrocampista, delantero, máximo 50 caracteres)
        dorsal (int): Número de dorsal del jugador (entre 1 y 99)
        activo (bool): Indica si el jugador está activo en el equipo (por defecto True)
    """
    id_usuario: int
    id_equipo: int
    posicion: str = Field(..., max_length=50)
    dorsal: int = Field(..., ge=1, le=99)  # Validación: dorsal entre 1 y 99
    activo: bool = True  # Por defecto, el jugador está activo

class JugadorCreate(JugadorBase):
    """
    Schema para crear un nuevo jugador.
    Usado en el endpoint POST /jugadores/
    Hereda todos los campos de JugadorBase como requeridos.
    """
    pass

class JugadorUpdate(BaseModel):
    """
    Schema para actualizar un jugador existente.
    Usado en el endpoint PUT/PATCH /jugadores/{id_jugador}
    
    Attributes:
        id_usuario (int | None): ID del usuario asociado al jugador
        id_equipo (int | None): ID del equipo al que pertenece el jugador
        posicion (str | None): Posición del jugador en el campo (máximo 50 caracteres)
        dorsal (int | None): Número de dorsal del jugador (entre 1 y 99)
        activo (bool | None): Indica si el jugador está activo en el equipo
    """
    id_usuario: int | None = None
    id_equipo: int | None = None
    posicion: str | None = Field(None, max_length=50)
    dorsal: int | None = Field(None, ge=1, le=99)  # Validación: dorsal entre 1 y 99
    activo: bool | None = None

class JugadorResponse(BaseModel):
    """
    Schema de respuesta para un jugador.
    Usado en las respuestas de los endpoints GET /jugadores/
    
    Attributes:
        id_jugador (int): Identificador único del jugador
        id_usuario (int): ID del usuario asociado al jugador
        id_equipo (int): ID del equipo al que pertenece el jugador
        posicion (str): Posición del jugador en el campo
        dorsal (int): Número de dorsal del jugador
        activo (bool): Indica si el jugador está activo en el equipo
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_jugador: int
    id_usuario: int
    id_equipo: int
    posicion: str
    dorsal: int
    activo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
