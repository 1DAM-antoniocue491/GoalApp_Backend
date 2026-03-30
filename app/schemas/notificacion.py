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
        mensaje (str): Contenido del mensaje de la notificación
        leida (bool): Indica si la notificación ha sido leída (por defecto False)
    """
    id_usuario: int
    mensaje: str
    leida: bool = False  # Por defecto, la notificación no está leída

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
        mensaje (str | None): Contenido del mensaje de la notificación
        leida (bool | None): Indica si la notificación ha sido leída
    """
    id_usuario: int | None = None
    mensaje: str | None = None
    leida: bool | None = None  # Típicamente se actualiza este campo para marcar como leída

class NotificacionResponse(BaseModel):
    """
    Schema de respuesta para una notificación.
    Usado en las respuestas de los endpoints GET /notificaciones/
    
    Attributes:
        id_notificacion (int): Identificador único de la notificación
        id_usuario (int): ID del usuario destinatario de la notificación
        mensaje (str): Contenido del mensaje de la notificación
        leida (bool): Indica si la notificación ha sido leída
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización del registro
    """
    id_notificacion: int
    id_usuario: int
    mensaje: str
    leida: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite crear el schema desde objetos ORM de SQLAlchemy
