"""
Schemas de validación para el recurso LigaConfiguracion.
Define los modelos Pydantic para request/response de la API relacionados con la configuración de ligas.
"""
from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import Optional


class LigaConfiguracionBase(BaseModel):
    """
    Schema base de LigaConfiguracion con campos comunes.

    Attributes:
        hora_partidos (time): Hora habitual de los partidos
        max_equipos (int): Máximo de equipos en la liga
        min_jugadores_equipo (int): Mínimo de jugadores por equipo
        min_partidos_entre_equipos (int): Mínimo de partidos entre equipos
    """
    hora_partidos: time = Field(default=time(17, 0), description="Hora habitual de los partidos")
    max_equipos: int = Field(default=20, ge=2, le=100, description="Máximo de equipos en la liga")
    min_jugadores_equipo: int = Field(default=7, ge=5, le=50, description="Mínimo de jugadores por equipo")
    min_partidos_entre_equipos: int = Field(default=2, ge=1, le=10, description="Mínimo de partidos entre equipos")


class LigaConfiguracionCreate(LigaConfiguracionBase):
    """
    Schema para crear la configuración de una liga.
    Usado en el endpoint POST /ligas/{id}/configuracion

    Hereda todos los campos de LigaConfiguracionBase.
    """
    pass


class LigaConfiguracionUpdate(BaseModel):
    """
    Schema para actualizar la configuración de una liga.
    Usado en el endpoint PUT /ligas/{id}/configuracion

    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    hora_partidos: Optional[time] = Field(None, description="Hora habitual de los partidos")
    max_equipos: Optional[int] = Field(None, ge=2, le=100, description="Máximo de equipos en la liga")
    min_jugadores_equipo: Optional[int] = Field(None, ge=5, le=50, description="Mínimo de jugadores por equipo")
    min_partidos_entre_equipos: Optional[int] = Field(None, ge=1, le=10, description="Mínimo de partidos entre equipos")


class LigaConfiguracionResponse(BaseModel):
    """
    Schema de respuesta para la configuración de una liga.
    Usado en las respuestas de los endpoints GET /ligas/{id}/configuracion

    Attributes:
        id_configuracion (int): Identificador único de la configuración
        id_liga (int): ID de la liga asociada
        hora_partidos (time): Hora habitual de los partidos
        max_equipos (int): Máximo de equipos en la liga
        min_jugadores_equipo (int): Mínimo de jugadores por equipo
        min_partidos_entre_equipos (int): Mínimo de partidos entre equipos
        created_at (datetime): Fecha y hora de creación
        updated_at (datetime): Fecha y hora de última actualización
    """
    id_configuracion: int
    id_liga: int
    hora_partidos: time
    max_equipos: int
    min_jugadores_equipo: int
    min_partidos_entre_equipos: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True