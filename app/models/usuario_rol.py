# app/models/usuario_rol.py
"""
Modelo de relación Usuario-Rol (tabla intermedia).
Implementa la relación N:N entre usuarios y roles.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from ..database.connection import Base


class UsuarioRol(Base):
    """
    Modelo ORM para la tabla 'usuario_rol'.
    
    Tabla intermedia que permite asignar múltiples roles a un usuario.
    Un usuario puede tener varios roles simultáneamente (ej: Coach + Player).
    
    Attributes:
        id_usuario_rol (int): Identificador único de la relación (Primary Key)
        id_usuario (int): ID del usuario (Foreign Key a usuarios.id_usuario)
        id_rol (int): ID del rol (Foreign Key a roles.id_rol)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "usuario_rol"

    # Clave primaria
    id_usuario_rol = Column(Integer, primary_key=True, index=True)

    # Claves foráneas: relación entre usuario y rol
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
