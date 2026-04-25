"""
Schemas de validación para el recurso Notificacion.
Define los modelos Pydantic para request/response de la API relacionados con notificaciones del sistema.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class NotificacionBase(BaseModel):
    """
    Schema base de Notificacion con campos comunes.
    Usado como clase base para herencia.

    Attributes:
        id_usuario (int): ID del usuario destinatario de la notificación
        tipo (str): Tipo de notificación (partido_finalizado, convocatoria, etc.)
        titulo (str): Título corto de la notificación
        mensaje (str): Contenido del mensaje de la notificación
        leida (bool): Indica si la notificación ha sido leída (por defecto False)
        id_referencia (int | None): ID del partido/liga/equipo relacionado
        tipo_referencia (str | None): Tipo de referencia ("partido", "liga", "equipo")
    """
    id_usuario: int
    tipo: str
    titulo: str
    mensaje: str
    leida: bool = False
    id_referencia: int | None = None
    tipo_referencia: str | None = None

class NotificacionCreate(NotificacionBase):
    """
    Schema para crear una nueva notificación.
    Usado en el endpoint POST /notificaciones/
    Hereda todos los campos de NotificacionBase como requeridos.
    """
    pass

class NotificacionUpdate(BaseModel):
    """
    Schema para actualizar una notificación existente.
    Usado en el endpoint PUT/PATCH /notificaciones/{id_notificacion}

    Attributes:
        id_usuario (int | None): ID del usuario destinatario de la notificación
        tipo (str | None): Tipo de notificación
        titulo (str | None): Título corto de la notificación
        mensaje (str | None): Contenido del mensaje de la notificación
        leida (bool | None): Indica si la notificación ha sido leída
        id_referencia (int | None): ID del partido/liga/equipo relacionado
        tipo_referencia (str | None): Tipo de referencia
    """
    id_usuario: int | None = None
    tipo: str | None = None
    titulo: str | None = None
    mensaje: str | None = None
    leida: bool | None = None
    id_referencia: int | None = None
    tipo_referencia: str | None = None

class NotificacionResponse(BaseModel):
    """
    Schema de respuesta para una notificación.
    Usado en las respuestas de los endpoints GET /notificaciones/

    Attributes:
        id_notificacion (int): Identificador único de la notificación
        id_usuario (int): ID del usuario destinatario de la notificación
        tipo (str): Tipo de notificación (partido_finalizado, convocatoria, etc.)
        titulo (str): Título corto de la notificación
        mensaje (str): Contenido del mensaje de la notificación
        leida (bool): Indica si la notificación ha sido leída
        id_referencia (int | None): ID del partido/liga/equipo relacionado
        tipo_referencia (str | None): Tipo de referencia
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_notificacion: int
    id_usuario: int
    tipo: str
    titulo: str
    mensaje: str
    leida: bool
    id_referencia: int | None
    tipo_referencia: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
