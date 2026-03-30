"""
Schemas de validación para el recurso Partido.
Define los modelos Pydantic para request/response de la API relacionados con partidos de fútbol.
"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class EstadoPartido(str, Enum):
    """
    Enum de estados posibles de un partido.
    
    Values:
        programado: El partido está programado pero aún no ha comenzado
        en_juego: El partido se está jugando actualmente
        finalizado: El partido ha concluido
        cancelado: El partido fue cancelado
    """
    programado = "programado"
    en_juego = "en_juego"
    finalizado = "finalizado"
    cancelado = "cancelado"

class PartidoBase(BaseModel):
    """
    Schema base de Partido con campos comunes.
    Usado como clase base para herencia.
    
    Attributes:
        id_liga (int): ID de la liga a la que pertenece el partido
        id_equipo_local (int): ID del equipo que juega como local
        id_equipo_visitante (int): ID del equipo que juega como visitante
        fecha (datetime): Fecha y hora del partido
        estado (EstadoPartido): Estado actual del partido (programado, en_juego, finalizado, cancelado)
        goles_local (int | None): Goles marcados por el equipo local (None si el partido no ha comenzado)
        goles_visitante (int | None): Goles marcados por el equipo visitante (None si el partido no ha comenzado)
    """
    id_liga: int
    id_equipo_local: int
    id_equipo_visitante: int
    fecha: datetime
    estado: EstadoPartido
    goles_local: int | None = None  # Inicia en None hasta que se juegue el partido
    goles_visitante: int | None = None  # Inicia en None hasta que se juegue el partido

class PartidoCreate(PartidoBase):
    """
    Schema para crear un nuevo partido.
    Usado en el endpoint POST /partidos/
    Hereda todos los campos de PartidoBase como requeridos.
    """
    pass

class PartidoUpdate(BaseModel):
    """
    Schema para actualizar un partido existente.
    Usado en el endpoint PUT/PATCH /partidos/{id_partido}
    
    Attributes:
        id_liga (int | None): ID de la liga a la que pertenece el partido
        id_equipo_local (int | None): ID del equipo que juega como local
        id_equipo_visitante (int | None): ID del equipo que juega como visitante
        fecha (datetime | None): Fecha y hora del partido
        estado (EstadoPartido | None): Estado actual del partido
        goles_local (int | None): Goles marcados por el equipo local
        goles_visitante (int | None): Goles marcados por el equipo visitante
    """
    id_liga: int | None = None
    id_equipo_local: int | None = None
    id_equipo_visitante: int | None = None
    fecha: datetime | None = None
    estado: EstadoPartido | None = None
    goles_local: int | None = None
    goles_visitante: int | None = None

class PartidoResponse(BaseModel):
    """
    Schema de respuesta para un partido.
    Usado en las respuestas de los endpoints GET /partidos/
    
    Attributes:
        id_partido (int): Identificador único del partido
        id_liga (int): ID de la liga a la que pertenece el partido
        id_equipo_local (int): ID del equipo que juega como local
        id_equipo_visitante (int): ID del equipo que juega como visitante
        fecha (datetime): Fecha y hora del partido
        estado (EstadoPartido): Estado actual del partido
        goles_local (int | None): Goles marcados por el equipo local
        goles_visitante (int | None): Goles marcados por el equipo visitante
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_partido: int
    id_liga: int
    id_equipo_local: int
    id_equipo_visitante: int
    fecha: datetime
    estado: EstadoPartido
    goles_local: int | None
    goles_visitante: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
