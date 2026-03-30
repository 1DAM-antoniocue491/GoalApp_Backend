# app/schemas/seguimiento.py
"""
Schemas de seguimiento de ligas.
Define los modelos Pydantic para el seguimiento de ligas por usuarios.
"""
from pydantic import BaseModel
from datetime import datetime


class SeguimientoResponse(BaseModel):
    """
    Schema de respuesta para un seguimiento.

    Attributes:
        id_seguimiento (int): ID del seguimiento
        id_usuario (int): ID del usuario
        id_liga (int): ID de la liga
        created_at (datetime): Fecha de creación del seguimiento
    """
    id_seguimiento: int
    id_usuario: int
    id_liga: int
    created_at: datetime

    class Config:
        from_attributes = True


class LigaSeguidaResponse(BaseModel):
    """
    Schema de respuesta para una liga seguida.

    Incluye información básica de la liga.

    Attributes:
        id_liga (int): ID de la liga
        nombre (str): Nombre de la liga
        temporada (str): Temporada de la liga
        activa (bool): Si la liga está activa
    """
    id_liga: int
    nombre: str
    temporada: str
    activa: bool

    class Config:
        from_attributes = True