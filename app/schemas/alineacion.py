# app/schemas/alineacion.py
"""
Schemas de AlineacionPartido para la gestión de alineaciones de jugadores en partidos.
Define los modelos Pydantic para crear y consultar alineaciones.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class AlineacionBase(BaseModel):
    """
    Schema base para una alineación de partido.

    Attributes:
        id_partido (int): ID del partido
        id_jugador (int): ID del jugador
        id_posicion (int): ID de la posición en el campo
        titular (bool): Si el jugador es titular (default: False)
    """
    id_partido: int = Field(..., description="ID del partido")
    id_jugador: int = Field(..., description="ID del jugador")
    id_posicion: int = Field(..., description="ID de la posición en el campo")
    titular: bool = Field(default=False, description="Si el jugador es titular")


class AlineacionCreate(AlineacionBase):
    """
    Schema para crear una alineación de partido.

    Hereda todos los campos de AlineacionBase.
    """
    pass


class AlineacionUpdate(BaseModel):
    """
    Schema para actualizar una alineación existente.

    Todos los campos son opcionales para actualización parcial.

    Attributes:
        id_posicion (int | None): Nueva posición del jugador
        titular (bool | None): Nuevo estado de titular
    """
    id_posicion: Optional[int] = Field(None, description="ID de la posición en el campo")
    titular: Optional[bool] = Field(None, description="Si el jugador es titular")


class AlineacionResponse(BaseModel):
    """
    Schema de respuesta para una alineación de partido.

    Attributes:
        id_alineacion (int): ID de la alineación
        id_partido (int): ID del partido
        id_jugador (int): ID del jugador
        id_posicion (int): ID de la posición
        titular (bool): Si el jugador es titular
        created_at (datetime): Fecha de creación
        updated_at (datetime): Fecha de última actualización
    """
    id_alineacion: int
    id_partido: int
    id_jugador: int
    id_posicion: int
    titular: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JugadorAlineadoResponse(BaseModel):
    """
    Schema de respuesta con información del jugador alineado.

    Incluye información del jugador y su posición en el partido.

    Attributes:
        id_alineacion (int): ID de la alineación
        id_jugador (int): ID del jugador
        nombre (str): Nombre del jugador
        dorsal (int): Número de dorsal
        posicion (str): Posición del jugador en el campo
        id_posicion (int): ID de la posición
        titular (bool): Si es titular
    """
    id_alineacion: int
    id_jugador: int
    nombre: str
    dorsal: int
    posicion_jugador: str  # Posición habitual del jugador
    posicion_campo: str  # Posición en el campo en este partido
    id_posicion: int
    titular: bool


class AlineacionPartidoResponse(BaseModel):
    """
    Schema de respuesta para la alineación completa de un partido.

    Attributes:
        id_partido (int): ID del partido
        equipo_local (str): Nombre del equipo local
        equipo_visitante (str): Nombre del equipo visitante
        titulares_local (List[JugadorAlineadoResponse]): Titulares del equipo local
        suplentes_local (List[JugadorAlineadoResponse]): Suplentes del equipo local
        titulares_visitante (List[JugadorAlineadoResponse]): Titulares del equipo visitante
        suplentes_visitante (List[JugadorAlineadoResponse]): Suplentes del equipo visitante
    """
    id_partido: int
    equipo_local: str
    equipo_visitante: str
    titulares_local: List[JugadorAlineadoResponse]
    suplentes_local: List[JugadorAlineadoResponse]
    titulares_visitante: List[JugadorAlineadoResponse]
    suplentes_visitante: List[JugadorAlineadoResponse]


class AlineacionEquipoResponse(BaseModel):
    """
    Schema de respuesta para la alineación de un equipo específico.

    Attributes:
        id_partido (int): ID del partido
        id_equipo (int): ID del equipo
        nombre_equipo (str): Nombre del equipo
        titulares (List[JugadorAlineadoResponse]): Jugadores titulares
        suplentes (List[JugadorAlineadoResponse]): Jugadores suplentes
    """
    id_partido: int
    id_equipo: int
    nombre_equipo: str
    titulares: List[JugadorAlineadoResponse]
    suplentes: List[JugadorAlineadoResponse]


class AlineacionBulkCreate(BaseModel):
    """
    Schema para crear múltiples alineaciones de un partido.

    Attributes:
        id_partido (int): ID del partido
        alineaciones (List[AlineacionBase]): Lista de alineaciones a crear
    """
    id_partido: int = Field(..., description="ID del partido")
    alineaciones: List[AlineacionBase] = Field(..., description="Lista de alineaciones")