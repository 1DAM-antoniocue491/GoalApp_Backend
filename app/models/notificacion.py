# app/models/notificacion.py
"""
Modelo de Notificación para enviar mensajes a usuarios.
Gestiona notificaciones push y mensajes del sistema.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Notificacion(Base):
    """
    Modelo ORM para la tabla 'notificaciones'.

    Gestiona las notificaciones enviadas a los usuarios sobre eventos relevantes:
    - Partidos próximos
    - Resultados de partidos
    - Cambios en el equipo
    - Anuncios del administrador

    Attributes:
        id_notificacion (int): Identificador único de la notificación (Primary Key)
        id_usuario (int): ID del usuario destinatario (Foreign Key)
        mensaje (text): Contenido del mensaje de notificación
        leida (bool): Si el usuario ha leído la notificación (default: False)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        usuario (Usuario): Relación con el usuario destinatario
    """
    __tablename__ = "notificaciones"

    # Clave primaria
    id_notificacion = Column(Integer, primary_key=True, index=True)

    # Relación: usuario destinatario
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Información de la notificación
    mensaje = Column(Text, nullable=False)  # Contenido del mensaje (puede ser largo)
    leida = Column(Boolean, nullable=False, default=False)  # Estado de lectura

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    usuario = relationship("Usuario", lazy="selectin")
