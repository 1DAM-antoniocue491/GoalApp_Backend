"""
Schemas de validación para el recurso EstadoJugadorPartido.
Define los modelos Pydantic para el estado de jugadores durante un partido.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EstadoJugadorEnum(str, Enum):
    """
    Enum de estados posibles de un jugador durante un partido.

    Values:
        jugando: El jugador está en el campo de juego
        suplente: El jugador está en el banquillo (disponible)
        lesionado: El jugador está lesionado (no puede continuar)
        expulsado: El jugador fue expulsado (no puede continuar)
    """
    jugando = "jugando"
    suplente = "suplente"
    lesionado = "lesionado"
    expulsado = "expulsado"


class EstadoJugadorPartidoBase(BaseModel):
    """
    Schema base de EstadoJugadorPartido con campos comunes.

    Attributes:
        id_partido (int): ID del partido
        id_jugador (int): ID del jugador
        id_equipo (int): ID del equipo
        estado (EstadoJugadorEnum): Estado actual ('jugando', 'suplente', etc.)
        minuto_entrada (int | None): Minuto cuando entró al campo
        minuto_salida (int | None): Minuto cuando salió del campo
    """
    id_partido: int
    id_jugador: int
    id_equipo: int
    estado: EstadoJugadorEnum
    minuto_entrada: int | None = None
    minuto_salida: int | None = None


class EstadoJugadorPartidoCreate(EstadoJugadorPartidoBase):
    """
    Schema para crear un nuevo estado de jugador.
    Usado en la inicialización al inicio del partido.
    """
    pass


class EstadoJugadorPartidoUpdate(BaseModel):
    """
    Schema para actualizar el estado de un jugador.
    Usado cuando se registra una sustitución.

    Attributes:
        estado (EstadoJugadorEnum | None): Nuevo estado
        minuto_entrada (int | None): Minuto de entrada
        minuto_salida (int | None): Minuto de salida
    """
    estado: EstadoJugadorEnum | None = None
    minuto_entrada: int | None = None
    minuto_salida: int | None = None


class EstadoJugadorPartidoResponse(BaseModel):
    """
    Schema de respuesta para el estado de un jugador.

    Attributes:
        id_estado (int): ID del registro
        id_partido (int): ID del partido
        id_jugador (int): ID del jugador
        id_equipo (int): ID del equipo
        estado (EstadoJugadorEnum): Estado actual
        minuto_entrada (int | None): Minuto de entrada
        minuto_salida (int | None): Minuto de salida
        created_at (datetime): Fecha de creación
        updated_at (datetime): Fecha de actualización
    """
    id_estado: int
    id_partido: int
    id_jugador: int
    id_equipo: int
    estado: EstadoJugadorEnum
    minuto_entrada: int | None
    minuto_salida: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JugadoresEnCampoResponse(BaseModel):
    """
    Respuesta con los jugadores que están actualmente en el campo.

    Attributes:
        jugando (list[int]): Lista de IDs de jugadores que están jugando
        suplentes (list[int]): Lista de IDs de jugadores que están en el banquillo
    """
    jugando: list[int]
    suplentes: list[int]
