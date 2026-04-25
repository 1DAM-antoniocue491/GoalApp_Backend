# app/models/notificacion.py
"""
Modelo de Notificación para enviar mensajes a usuarios.
Gestiona notificaciones push y mensajes del sistema.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
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
        tipo (str): Tipo de notificación (partido_finalizado, convocatoria, etc.)
        titulo (str): Título corto de la notificación
        mensaje (text): Contenido del mensaje de notificación
        leida (bool): Si el usuario ha leído la notificación (default: False)
        id_referencia (int | None): ID del partido/liga/equipo relacionado
        tipo_referencia (str | None): Tipo de referencia ("partido", "liga", "equipo")
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        usuario (Usuario): Relación con el usuario destinatario
    """
    __tablename__ = "notificaciones"

    # Clave primaria
    id_notificacion = Column(Integer, primary_key=True)

    # Relación: usuario destinatario
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Información de la notificación
    tipo = Column(String(50), nullable=False)  # Tipo: partido_finalizado, convocatoria, etc.
    titulo = Column(String(100), nullable=False)  # Título corto para UI
    mensaje = Column(Text, nullable=False)  # Contenido del mensaje (puede ser largo)
    leida = Column(Boolean, nullable=False, default=False)  # Estado de lectura
    id_referencia = Column(Integer, nullable=True)  # ID del partido/liga/equipo relacionado
    tipo_referencia = Column(String(50), nullable=True)  # "partido", "liga", "equipo"

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    usuario = relationship("Usuario", lazy="raise")
