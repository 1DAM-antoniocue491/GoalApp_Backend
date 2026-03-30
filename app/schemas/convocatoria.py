# app/schemas/convocatoria.py
"""
Schemas de Convocatoria para la gestión de convocatorias de partidos.
Define los modelos Pydantic para crear y consultar convocatorias.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class ConvocatoriaItemBase(BaseModel):
    """
    Schema base para un item de convocatoria.

    Attributes:
        id_jugador (int): ID del jugador
        es_titular (bool): Si el jugador es titular (default: False)
    """
    id_jugador: int = Field(..., description="ID del jugador")
    es_titular: bool = Field(default=False, description="Si el jugador es titular")


class ConvocatoriaCreate(BaseModel):
    """
    Schema para crear una convocatoria completa de un partido.

    Attributes:
        id_partido (int): ID del partido
        jugadores (List[ConvocatoriaItemBase]): Lista de jugadores convocados
    """
    id_partido: int = Field(..., description="ID del partido")
    jugadores: List[ConvocatoriaItemBase] = Field(..., description="Lista de jugadores convocados")


class ConvocatoriaResponse(BaseModel):
    """
    Schema de respuesta para un item de convocatoria.

    Attributes:
        id_convocatoria (int): ID de la convocatoria
        id_partido (int): ID del partido
        id_jugador (int): ID del jugador
        es_titular (bool): Si el jugador es titular
        created_at (datetime): Fecha de creación
    """
    id_convocatoria: int
    id_partido: int
    id_jugador: int
    es_titular: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JugadorConvocadoResponse(BaseModel):
    """
    Schema de respuesta con información del jugador convocado.

    Attributes:
        id_jugador (int): ID del jugador
        nombre (str): Nombre del jugador
        dorsal (int): Dorsal del jugador
        posicion (str): Posición del jugador
        es_titular (bool): Si es titular
    """
    id_jugador: int
    nombre: str
    dorsal: int
    posicion: str
    es_titular: bool


class ConvocatoriaPartidoResponse(BaseModel):
    """
    Schema de respuesta para la convocatoria completa de un partido.

    Attributes:
        id_partido (int): ID del partido
        titulares (List[JugadorConvocadoResponse]): Jugadores titulares
        suplentes (List[JugadorConvocadoResponse]): Jugadores suplentes
    """
    id_partido: int
    titulares: List[JugadorConvocadoResponse]
    suplentes: List[JugadorConvocadoResponse]