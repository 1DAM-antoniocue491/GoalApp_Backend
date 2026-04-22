# app/models/usuario_rol.py
"""
Modelo de relación Usuario-Rol (tabla intermedia).
Implementa la relación N:N entre usuarios y roles, con asociación a una liga específica.

Un usuario puede tener diferentes roles en diferentes ligas:
- Ejemplo: admin en Liga A, entrenador en Liga B
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class UsuarioRol(Base):
    """
    Modelo ORM para la tabla 'usuario_rol'.

    Tabla intermedia que permite asignar múltiples roles a un usuario
    en el contexto de una liga específica.

    Attributes:
        id_usuario_rol (int): Identificador único de la relación (Primary Key)
        id_usuario (int): ID del usuario (Foreign Key a usuarios.id_usuario)
        id_rol (int): ID del rol (Foreign Key a roles.id_rol)
        id_liga (int): ID de la liga (Foreign Key a ligas.id_liga)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "usuario_rol"

    # Clave primaria
    id_usuario_rol = Column(Integer, primary_key=True)

    # Claves foráneas: relación entre usuario, rol y liga
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)

    # Estado: si el usuario está activo en la liga
    activo = Column(Integer, default=1, nullable=False)  # 1 = activo, 0 = pendiente

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    liga = relationship("Liga", back_populates="usuario_roles", lazy="raise")
