# app/models/token_recuperacion.py
"""
Modelo de Token de Recuperación para gestión de contraseñas olvidadas.
Almacena tokens temporales para el flujo de recuperación de contraseña.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, text
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
    id_token = Column(Integer, primary_key=True, index=True)

    # Relación: usuario solicitante
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Token de recuperación
    token = Column(String(255), nullable=False, unique=True, index=True)
    fecha_expiracion = Column(DateTime, nullable=False)
    usado = Column(Boolean, nullable=False, default=False)

    # Auditoría: fecha de creación
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False)

    # Relaciones ORM
    usuario = relationship("Usuario", lazy="selectin")