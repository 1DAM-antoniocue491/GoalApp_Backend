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
    """
    id_partido: int
    id_jugador: int
    tipo_evento: TipoEvento
    minuto: int = Field(..., ge=1, le=120)  # Validación: minuto entre 1 y 120

class EventoPartidoCreate(EventoPartidoBase):
    """
    Schema para crear un nuevo evento de partido.
    Usado en el endpoint POST /eventos-partido/
    Hereda todos los campos de EventoPartidoBase como requeridos.
    """
    pass

class EventoPartidoUpdate(BaseModel):
    """
    Schema para actualizar un evento de partido existente.
    Usado en el endpoint PUT/PATCH /eventos-partido/{id_evento}
    
    Attributes:
        id_partido (int | None): ID del partido donde ocurrió el evento
        id_jugador (int | None): ID del jugador involucrado en el evento
        tipo_evento (TipoEvento | None): Tipo de evento (gol, tarjeta, cambio, mvp)
        minuto (int | None): Minuto del partido en que ocurrió (entre 1 y 120)
    """
    id_partido: int | None = None
    id_jugador: int | None = None
    tipo_evento: TipoEvento | None = None
    minuto: int | None = Field(None, ge=1, le=120)  # Validación: minuto entre 1 y 120

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
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_evento: int
    id_partido: int
    id_jugador: int
    tipo_evento: TipoEvento
    minuto: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
