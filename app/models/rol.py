# app/models/rol.py
"""
Modelo de Rol para el sistema de autorización.
Define los diferentes roles de usuario en la aplicación.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Rol(Base):
    """
    Modelo ORM para la tabla 'roles'.

    Define los roles disponibles en el sistema:
    - Admin: Administrador global
    - Coach: Entrenador de equipo
    - Delegate: Delegado de campo
    - Player: Jugador
    - Viewer: Espectador

    Attributes:
        id_rol (int): Identificador único del rol (Primary Key)
        nombre (str): Nombre del rol (máx. 50 caracteres, único)
        descripcion (str): Descripción detallada del rol (opcional, máx. 255 caracteres)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        usuarios (list): Lista de usuarios con este rol (relación N:N)
    """
    __tablename__ = "roles"

    # Clave primaria
    id_rol = Column(Integer, primary_key=True)

    # Información del rol
    nombre = Column(String(50), nullable=False, unique=True)  # Ejemplo: "Admin", "Coach"
    descripcion = Column(String(255), nullable=True)  # Descripción opcional del rol

    # Auditoría: fechas de creación y actualización
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    usuarios = relationship("Usuario", secondary="usuario_rol", back_populates="roles", lazy="raise")
