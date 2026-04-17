"""
Schemas de validación para el recurso LigaConfiguracion.
"""
from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import Optional


class LigaConfiguracionBase(BaseModel):
    hora_partidos: time = Field(default=time(17, 0), description="Hora habitual de los partidos")
    min_equipos: int = Field(default=2, ge=2, le=50, description="Mínimo de equipos en la liga")
    max_equipos: int = Field(default=20, ge=2, le=100, description="Máximo de equipos en la liga")
    min_convocados: int = Field(default=14, ge=7, le=50, description="Mínimo de jugadores convocados por partido")
    max_convocados: int = Field(default=22, ge=7, le=50, description="Máximo de jugadores convocados por partido")
    min_plantilla: int = Field(default=11, ge=7, le=50, description="Mínimo de jugadores en plantilla")
    max_plantilla: int = Field(default=25, ge=7, le=50, description="Máximo de jugadores en plantilla")
    min_jugadores_equipo: int = Field(default=7, ge=5, le=50, description="Mínimo de jugadores por equipo para jugar")
    min_partidos_entre_equipos: int = Field(default=2, ge=1, le=10, description="Mínimo de partidos entre equipos")
    minutos_partido: int = Field(default=90, ge=30, le=120, description="Minutos de duración del partido")
    max_partidos: int = Field(default=30, ge=1, le=100, description="Cantidad máxima de partidos")


class LigaConfiguracionCreate(LigaConfiguracionBase):
    pass


class LigaConfiguracionUpdate(BaseModel):
    hora_partidos: Optional[time] = Field(None, description="Hora habitual de los partidos")
    min_equipos: Optional[int] = Field(None, ge=2, le=50, description="Mínimo de equipos en la liga")
    max_equipos: Optional[int] = Field(None, ge=2, le=100, description="Máximo de equipos en la liga")
    min_convocados: Optional[int] = Field(None, ge=7, le=50, description="Mínimo de jugadores convocados por partido")
    max_convocados: Optional[int] = Field(None, ge=7, le=50, description="Máximo de jugadores convocados por partido")
    min_plantilla: Optional[int] = Field(None, ge=7, le=50, description="Mínimo de jugadores en plantilla")
    max_plantilla: Optional[int] = Field(None, ge=7, le=50, description="Máximo de jugadores en plantilla")
    min_jugadores_equipo: Optional[int] = Field(None, ge=5, le=50, description="Mínimo de jugadores por equipo para jugar")
    min_partidos_entre_equipos: Optional[int] = Field(None, ge=1, le=10, description="Mínimo de partidos entre equipos")
    minutos_partido: Optional[int] = Field(None, ge=30, le=120, description="Minutos de duración del partido")
    max_partidos: Optional[int] = Field(None, ge=1, le=100, description="Cantidad máxima de partidos")


class LigaConfiguracionResponse(BaseModel):
    id_configuracion: int
    id_liga: int
    hora_partidos: time
    min_equipos: int
    max_equipos: int
    min_convocados: int
    max_convocados: int
    min_plantilla: int
    max_plantilla: int
    min_jugadores_equipo: int
    min_partidos_entre_equipos: int
    minutos_partido: int
    max_partidos: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True