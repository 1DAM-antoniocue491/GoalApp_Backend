# app/schemas/clasificacion.py
"""
Schemas de Clasificación para la respuesta del endpoint de clasificación.
Define la estructura de datos para mostrar la tabla de posiciones de una liga.
"""
from pydantic import BaseModel


class ClasificacionItem(BaseModel):
    """
    Schema para un elemento de la clasificación.

    Representa la posición de un equipo en la tabla de clasificación
    con todas sus estadísticas.

    Attributes:
        posicion (int): Posición en la tabla (1, 2, 3...)
        id_equipo (int): ID del equipo
        nombre_equipo (str): Nombre del equipo
        puntos (int): Puntos totales (victoria=3, empate=1)
        partidos_jugados (int): Total de partidos jugados
        victorias (int): Número de victorias
        empates (int): Número de empates
        derrotas (int): Número de derrotas
        goles_favor (int): Goles marcados
        goles_contra (int): Goles recibidos
        diferencia_goles (int): Diferencia entre goles a favor y en contra
    """
    posicion: int
    id_equipo: int
    nombre_equipo: str
    puntos: int
    partidos_jugados: int
    victorias: int
    empates: int
    derrotas: int
    goles_favor: int
    goles_contra: int
    diferencia_goles: int

    class Config:
        from_attributes = True