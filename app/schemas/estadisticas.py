# app/schemas/estadisticas.py
"""
Schemas para estadísticas de fútbol.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class SeasonStatsResponse(BaseModel):
    """Estadísticas generales de la temporada."""
    total_partidos: int = Field(..., description="Total de partidos jugados")
    total_goles: int = Field(..., description="Total de goles anotados")
    promedio_goles_por_partido: float = Field(..., description="Promedio de goles por partido")
    total_amarillas: int = Field(..., description="Total de tarjetas amarillas")
    total_rojas: int = Field(..., description="Total de tarjetas rojas")
    total_asistencias: int = Field(..., description="Total de asistencias")
    equipos_participantes: int = Field(..., description="Número de equipos participantes")
    jugadores_registrados: int = Field(..., description="Número de jugadores registrados")


class TopScorerResponse(BaseModel):
    """Respuesta para un goleador."""
    id_jugador: int = Field(..., description="ID del jugador")
    id_usuario: int = Field(..., description="ID del usuario")
    id_equipo: int = Field(..., description="ID del equipo")
    nombre: str = Field(..., description="Nombre del jugador")
    nombre_equipo: str = Field(..., description="Nombre del equipo")
    escudo_equipo: Optional[str] = Field(None, description="URL del escudo del equipo")
    goles: int = Field(..., description="Número de goles")
    partidos_jugados: int = Field(..., description="Partidos jugados")
    promedio_goles: float = Field(..., description="Promedio de goles por partido")


class MatchdayMVPResponse(BaseModel):
    """Respuesta para el MVP de la jornada."""
    id_jugador: int = Field(..., description="ID del jugador")
    id_usuario: int = Field(..., description="ID del usuario")
    nombre: str = Field(..., description="Nombre del jugador")
    nombre_equipo: str = Field(..., description="Nombre del equipo")
    escudo_equipo: Optional[str] = Field(None, description="URL del escudo del equipo")
    rating: float = Field(..., description="Rating del jugador")
    goles: int = Field(..., description="Goles en el partido")
    asistencias: int = Field(..., description="Asistencias en el partido")
    jornada: int = Field(..., description="Número de jornada")


class TeamGoalsStatsResponse(BaseModel):
    """Estadísticas de goles de un equipo."""
    id_equipo: int = Field(..., description="ID del equipo")
    nombre: str = Field(..., description="Nombre del equipo")
    escudo: Optional[str] = Field(None, description="URL del escudo del equipo")
    goles_favor: int = Field(..., description="Goles a favor")
    goles_contra: int = Field(..., description="Goles en contra")
    diferencia_goles: int = Field(..., description="Diferencia de goles")
    promedio_goles_favor: float = Field(..., description="Promedio de goles a favor por partido")
    partidos_jugados: int = Field(..., description="Partidos jugados")


class PlayerPersonalStatsResponse(BaseModel):
    """Estadísticas personales de un jugador."""
    id_jugador: int = Field(..., description="ID del jugador")
    id_usuario: int = Field(..., description="ID del usuario")
    nombre: str = Field(..., description="Nombre del jugador")
    nombre_equipo: str = Field(..., description="Nombre del equipo")
    escudo_equipo: Optional[str] = Field(None, description="URL del escudo del equipo")
    goles: int = Field(..., description="Goles marcados")
    asistencias: int = Field(..., description="Asistencias")
    tarjetas_amarillas: int = Field(..., description="Tarjetas amarillas recibidas")
    tarjetas_rojas: int = Field(..., description="Tarjetas rojas recibidas")
    partidos_jugados: int = Field(..., description="Partidos jugados")
    veces_mvp: int = Field(..., description="Veces que ha sido MVP")
