"""
Schemas de validación para el recurso Equipo.
Define los modelos Pydantic para request/response de la API relacionados con equipos de fútbol.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class EquipoBase(BaseModel):
    """
    Schema base de Equipo con campos comunes.
    Usado como clase base para herencia.

    Attributes:
        nombre (str): Nombre del equipo (máximo 100 caracteres)
        escudo (str | None): URL o path del escudo del equipo
        colores (str | None): Colores representativos del equipo (máximo 50 caracteres)
        id_liga (int): ID de la liga a la que pertenece el equipo
        id_entrenador (int | None): ID del usuario que actúa como entrenador
        id_delegado (int | None): ID del usuario que actúa como delegado
    """
    nombre: str = Field(..., max_length=100)
    escudo: str | None = Field(None, max_length=255)
    colores: str | None = Field(None, max_length=50)
    id_liga: int
    id_entrenador: int | None = None
    id_delegado: int | None = None

class EquipoCreate(EquipoBase):
    """
    Schema para crear un nuevo equipo.
    Usado en el endpoint POST /equipos/
    Hereda todos los campos de EquipoBase como requeridos.
    """
    pass

class EquipoUpdate(BaseModel):
    """
    Schema para actualizar un equipo existente.
    Usado en el endpoint PUT/PATCH /equipos/{id_equipo}
    
    Attributes:
        nombre (str | None): Nombre del equipo (máximo 100 caracteres)
        escudo (str | None): URL o path del escudo del equipo (máximo 255 caracteres)
        colores (str | None): Colores representativos del equipo (máximo 50 caracteres)
        id_liga (int | None): ID de la liga a la que pertenece el equipo
        id_entrenador (int | None): ID del usuario que actúa como entrenador
        id_delegado (int | None): ID del usuario que actúa como delegado
    """
    nombre: str | None = Field(None, max_length=100)
    escudo: str | None = Field(None, max_length=255)
    colores: str | None = Field(None, max_length=50)
    id_liga: int | None = None
    id_entrenador: int | None = None
    id_delegado: int | None = None

class EquipoResponse(BaseModel):
    """
    Schema de respuesta para un equipo.
    Usado en las respuestas de los endpoints GET /equipos/

    Attributes:
        id_equipo (int): Identificador único del equipo
        nombre (str): Nombre del equipo
        escudo (str | None): URL o path del escudo del equipo
        colores (str | None): Colores representativos del equipo
        id_liga (int): ID de la liga a la que pertenece el equipo
        id_entrenador (int): ID del usuario que actúa como entrenador
        id_delegado (int): ID del usuario que actúa como delegado
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_equipo: int
    nombre: str
    escudo: str | None
    colores: str | None
    id_liga: int
    id_entrenador: int
    id_delegado: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy


class EquipoRendimientoResponse(BaseModel):
    """
    Schema de respuesta para el rendimiento de un equipo.
    Incluye estadísticas de victorias, empates y derrotas calculadas desde los partidos.

    Attributes:
        id_equipo (int): Identificador único del equipo
        nombre (str): Nombre del equipo
        escudo (str | None): URL o path del escudo del equipo
        colores (str | None): Colores representativos del equipo
        id_liga (int): ID de la liga a la que pertenece el equipo
        partidos_jugados (int): Total de partidos jugados
        victorias (int): Número de victorias
        empates (int): Número de empates
        derrotas (int): Número de derrotas
        porcentaje_victorias (float): Porcentaje de victorias (0-100)
    """
    id_equipo: int
    nombre: str
    escudo: str | None
    colores: str | None
    id_liga: int
    partidos_jugados: int
    victorias: int
    empates: int
    derrotas: int
    porcentaje_victorias: float

    class Config:
        from_attributes = True
