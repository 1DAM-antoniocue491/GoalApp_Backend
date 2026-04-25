"""
Schemas de validación para el recurso EventoPartido.
Define los modelos Pydantic para request/response de la API relacionados con eventos durante un partido.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class TipoEvento(str, Enum):
    """
    Enum de tipos de eventos que pueden ocurrir durante un partido.

    Values:
        gol: Anotación de un gol
        tarjeta_amarilla: Tarjeta amarilla mostrada a un jugador
        tarjeta_roja: Tarjeta roja mostrada a un jugador
        cambio: Sustitución de un jugador
        mvp: Designación del jugador más valioso del partido
    """
    gol = "gol"
    tarjeta_amarilla = "tarjeta_amarilla"
    tarjeta_roja = "tarjeta_roja"
    cambio = "cambio"
    mvp = "mvp"

class EventoPartidoBase(BaseModel):
    """
    Schema base de EventoPartido con campos comunes.
    Usado como clase base para herencia.

    Attributes:
        id_partido (int): ID del partido donde ocurrió el evento
        id_jugador (int): ID del jugador involucrado en el evento
        tipo_evento (TipoEvento): Tipo de evento (gol, tarjeta, cambio, mvp)
        minuto (int): Minuto del partido en que ocurrió (entre 1 y 120 para incluir prórroga)
        puntuacion_mvp (float | None): Puntuación del MVP (0-10, solo para eventos tipo MVP)
        incidencias (str | None): Notas o incidencias del partido (solo para eventos tipo MVP)
    """
    id_partido: int
    id_jugador: int
    tipo_evento: TipoEvento
    minuto: int = Field(..., ge=1, le=120)  # Validación: minuto entre 1 y 120
    puntuacion_mvp: float | None = Field(None, ge=0, le=10)  # Solo para tipo_evento="mvp"
    incidencias: str | None = None  # Solo para tipo_evento="mvp"

class EventoPartidoCreate(EventoPartidoBase):
    """
    Schema para crear un nuevo evento de partido.
    Usado en el endpoint POST /eventos/

    Attributes:
        id_partido (int): ID del partido
        id_jugador (int): ID del jugador involucrado
        tipo_evento (TipoEvento): Tipo de evento
        minuto (int): Minuto del evento (1-120)
        id_jugador_sale (int | None): ID del jugador que sale (solo para sustituciones)
        puntuacion_mvp (float | None): Puntuación MVP (0-10, solo para tipo='mvp')
        incidencias (str | None): Notas adicionales (motivo de tarjeta, etc.)
    """
    id_jugador_sale: int | None = None  # Solo para tipo_evento='cambio'

class EventoPartidoUpdate(BaseModel):
    """
    Schema para actualizar un evento de partido existente.
    Usado en el endpoint PUT/PATCH /eventos-partido/{id_evento}

    Attributes:
        id_partido (int | None): ID del partido donde ocurrió el evento
        id_jugador (int | None): ID del jugador involucrado en el evento
        tipo_evento (TipoEvento | None): Tipo de evento (gol, tarjeta, cambio, mvp)
        minuto (int | None): Minuto del partido en que ocurrió (entre 1 y 120)
        puntuacion_mvp (float | None): Puntuación del MVP (0-10)
        incidencias (str | None): Notas o incidencias del partido
    """
    id_partido: int | None = None
    id_jugador: int | None = None
    tipo_evento: TipoEvento | None = None
    minuto: int | None = Field(None, ge=1, le=120)  # Validación: minuto entre 1 y 120
    puntuacion_mvp: float | None = Field(None, ge=0, le=10)
    incidencias: str | None = None

class EventoPartidoResponse(BaseModel):
    """
    Schema de respuesta para un evento de partido.
    Usado en las respuestas de los endpoints GET /eventos-partido/

    Attributes:
        id_evento (int): Identificador único del evento
        id_partido (int): ID del partido donde ocurrió el evento
        id_jugador (int): ID del jugador involucrado en el evento
        tipo_evento (TipoEvento): Tipo de evento (gol, tarjeta, cambio, mvp)
        minuto (int): Minuto del partido en que ocurrió
        puntuacion_mvp (float | None): Puntuación del MVP (0-10)
        incidencias (str | None): Notas o incidencias del partido
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_evento: int
    id_partido: int
    id_jugador: int
    tipo_evento: TipoEvento
    minuto: int
    puntuacion_mvp: float | None
    incidencias: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
