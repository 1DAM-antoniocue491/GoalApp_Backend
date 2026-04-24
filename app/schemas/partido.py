"""
Schemas de validación para el recurso Partido.
Define los modelos Pydantic para request/response de la API relacionados con partidos de fútbol.
"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum

class EstadoPartido(str, Enum):
    """
    Enum de estados posibles de un partido.

    Value:
        programado: El partido está programado pero aún no ha comenzado
        en_juego: El partido se está jugando actualmente
        finalizado: El partido ha concluido
        cancelado: El partido fue cancelado
    """
    programado = "programado"
    en_juego = "en_juego"
    finalizado = "finalizado"
    cancelado = "cancelado"

    @classmethod
    def _missing_(cls, value):
        """Permite aceptar valores con mayúsculas normalizándolos a minúsculas."""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value.lower() == value_lower:
                    return member
        return None

class PartidoBase(BaseModel):
    """
    Schema base de Partido con campos comunes.
    Usado como clase base para herencia.
    
    Attributes:
        id_liga (int): ID de la liga a la que pertenece el partido
        id_equipo_local (int): ID del equipo que juega como local
        id_equipo_visitante (int): ID del equipo que juega como visitante
        fecha (datetime): Fecha y hora del partido
        estado (EstadoPartido): Estado actual del partido (programado, en_juego, finalizado, cancelado)
        goles_local (int | None): Goles marcados por el equipo local (None si el partido no ha comenzado)
        goles_visitante (int | None): Goles marcados por el equipo visitante (None si el partido no ha comenzado)
    """
    id_liga: int
    id_equipo_local: int
    id_equipo_visitante: int
    fecha: datetime
    estado: EstadoPartido
    goles_local: int | None = None  # Inicia en None hasta que se juegue el partido
    goles_visitante: int | None = None  # Inicia en None hasta que se juegue el partido

class PartidoCreate(PartidoBase):
    """
    Schema para crear un nuevo partido.
    Usado en el endpoint POST /partidos/
    Hereda todos los campos de PartidoBase como requeridos.
    """
    pass

class PartidoUpdate(BaseModel):
    """
    Schema para actualizar un partido existente.
    Usado en el endpoint PUT/PATCH /partidos/{id_partido}
    
    Attributes:
        id_liga (int | None): ID de la liga a la que pertenece el partido
        id_equipo_local (int | None): ID del equipo que juega como local
        id_equipo_visitante (int | None): ID del equipo que juega como visitante
        fecha (datetime | None): Fecha y hora del partido
        estado (EstadoPartido | None): Estado actual del partido
        goles_local (int | None): Goles marcados por el equipo local
        goles_visitante (int | None): Goles marcados por el equipo visitante
    """
    id_liga: int | None = None
    id_equipo_local: int | None = None
    id_equipo_visitante: int | None = None
    fecha: datetime | None = None
    estado: EstadoPartido | None = None
    goles_local: int | None = None
    goles_visitante: int | None = None

class PartidoResponse(BaseModel):
    """
    Schema de respuesta para un partido.
    Usado en las respuestas de los endpoints GET /partidos/

    Attributes:
        id_partido (int): Identificador único del partido
        id_liga (int): ID de la liga a la que pertenece el partido
        id_equipo_local (int): ID del equipo que juega como local
        id_equipo_visitante (int): ID del equipo que juega como visitante
        fecha (datetime): Fecha y hora del partido
        estado (EstadoPartido): Estado actual del partido
        goles_local (int | None): Goles marcados por el equipo local
        goles_visitante (int | None): Goles marcados por el equipo visitante
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_partido: int
    id_liga: int
    id_equipo_local: int
    id_equipo_visitante: int
    fecha: datetime
    estado: EstadoPartido
    goles_local: int | None
    goles_visitante: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy


class CalendarCreateRequest(BaseModel):
    """
    Schema para crear calendario automático de una liga.
    Usado en el endpoint POST /partidos/ligas/{liga_id}/crear-calendario

    Attributes:
        tipo (str): Tipo de calendario - 'ida' (solo ida) o 'ida_vuelta' (ida y vuelta)
        fecha_inicio (str): Fecha de inicio en formato YYYY-MM-DD
        dias_partido (list[int]): Días de la semana para los partidos (1=Lunes, 0=Domingo)
        hora (str): Hora de los partidos en formato HH:MM
    """
    tipo: str  # 'ida' o 'ida_vuelta'
    fecha_inicio: str  # formato YYYY-MM-DD
    dias_partido: list[int]  # [1, 3, 5] = Lunes, Miércoles, Viernes
    hora: str  # formato HH:MM


class CalendarCreateResponse(BaseModel):
    """
    Schema de respuesta tras crear calendario automático.

    Attributes:
        mensaje (str): Mensaje de confirmación
        partidos_creados (int): Número de partidos creados
    """
    mensaje: str
    partidos_creados: int


class CalendarConfigResponse(BaseModel):
    """
    Schema de respuesta para configuración de calendario automático.
    Usado en el endpoint GET /partidos/ligas/{liga_id}/config-calendario

    Attributes:
        tipo (str): Tipo de calendario - 'ida' o 'ida_vuelta'
        fecha_inicio (str): Fecha de inicio en formato YYYY-MM-DD
        dias_partido (list[int]): Días de la semana para los partidos (1=Lunes, 0=Domingo)
        hora (str): Hora de los partidos en formato HH:MM
    """
    tipo: str
    fecha_inicio: str
    dias_partido: list[int]
    hora: str


class CalendarDeleteResponse(BaseModel):
    """
    Schema de respuesta tras eliminar calendario automático.

    Attributes:
        mensaje (str): Mensaje de confirmación
        partidos_eliminados (int): Número de partidos eliminados
        jornadas_eliminadas (int): Número de jornadas eliminadas
    """
    mensaje: str
    partidos_eliminados: int
    jornadas_eliminadas: int


class CalendarUpdateResponse(BaseModel):
    """
    Schema de respuesta tras actualizar calendario automático.

    Attributes:
        mensaje (str): Mensaje de confirmación
        partidos_creados (int): Número de partidos creados
        partidos_eliminados (int): Número de partidos eliminados
    """
    mensaje: str
    partidos_creados: int
    partidos_eliminados: int


class FinalizarPartidoRequest(BaseModel):
    """
    Schema para finalizar un partido.
    Usado en el endpoint PUT /partidos/{id}/finalizar

    Attributes:
        goles_local (int): Goles finales del equipo local
        goles_visitante (int): Goles finales del equipo visitante
        id_mvp (int): ID del jugador MVP del partido
        puntuacion_mvp (float): Puntuación del MVP (0-10)
        incidencias (str | None): Notas o incidencias opcionales del partido
    """
    goles_local: int = Field(..., ge=0)
    goles_visitante: int = Field(..., ge=0)
    id_mvp: int
    puntuacion_mvp: float = Field(..., ge=0, le=10)
    incidencias: str | None = None
