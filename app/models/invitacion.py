# app/models/invitacion.py
"""
Modelo de Invitación para gestión de invitaciones a ligas.
Almacena invitaciones temporales enviadas por email a usuarios.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Invitacion(Base):
    """
    Modelo ORM para la tabla 'invitaciones'.

    Gestiona invitaciones temporales utilizadas para invitar a usuarios
    a unirse a una liga con un rol específico.

    Attributes:
        id_invitacion (int): Identificador único de la invitación (Primary Key)
        token (str): Token único y seguro para la invitación
        email (str): Email del usuario invitado
        id_liga (int): ID de la liga (Foreign Key)
        id_equipo (int): ID del equipo (Foreign Key, nullable para rol viewer)
        id_rol (int): ID del rol asignado (Foreign Key)
        dorsal (str): Número de dorsal asignado
        posicion (str): Posición del jugador
        tipo_jugador (str): Tipo de jugador (titular, suplente, etc.)
        invitado_por (int): ID del usuario que envía la invitación (Foreign Key)
        fecha_expiracion (datetime): Fecha y hora de expiración del token
        usada (bool): Si la invitación ya fue utilizada (default: False)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "invitaciones"

    # Clave primaria
    id_invitacion = Column(Integer, primary_key=True)

    # Token y email
    token = Column(String(64), nullable=False, unique=True, index=True)
    email = Column(String(120), nullable=False, index=True)

    # Relación: liga, equipo, rol
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)
    id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=True)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)

    # Detalles de la invitación
    dorsal = Column(String(10), nullable=True)
    posicion = Column(String(50), nullable=True)
    tipo_jugador = Column(String(50), nullable=True)

    # Usuario que invita (admin de la liga)
    invitado_por = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Expiración y estado
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)
    usada = Column(Boolean, nullable=False, default=False)

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    liga = relationship("Liga", lazy="raise")
    equipo = relationship("Equipo", lazy="raise")
    rol = relationship("Rol", lazy="raise")
    invitador = relationship("Usuario", lazy="raise", foreign_keys=[invitado_por])
