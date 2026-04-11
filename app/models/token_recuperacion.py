# app/models/token_recuperacion.py
"""
Modelo de Token de Recuperación para gestión de contraseñas olvidadas.
Almacena tokens temporales para el flujo de recuperación de contraseña.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class TokenRecuperacion(Base):
    """
    Modelo ORM para la tabla 'tokens_recuperacion'.

    Gestiona tokens temporales utilizados para el flujo de recuperación
    de contraseña cuando un usuario olvida su contraseña.

    Attributes:
        id_token (int): Identificador único del token (Primary Key)
        id_usuario (int): ID del usuario que solicita recuperación (Foreign Key)
        token (str): Token único y seguro para la recuperación
        fecha_expiracion (datetime): Fecha y hora de expiración del token
        usado (bool): Si el token ya fue utilizado (default: False)
        created_at (datetime): Fecha y hora de creación del registro
        usuario (Usuario): Relación con el usuario solicitante
    """
    __tablename__ = "tokens_recuperacion"

    # Clave primaria
    id_token = Column(Integer, primary_key=True)

    # Relación: usuario solicitante
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Token de recuperación
    token = Column(String(255), nullable=False, unique=True, index=True)
    fecha_expiracion = Column(DateTime, nullable=False)
    usado = Column(Boolean, nullable=False, default=False)

    # Auditoría: fecha de creación
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    usuario = relationship("Usuario", lazy="raise")