# app/models/usuario_sigue_liga.py
"""
Modelo de relación Usuario-Sigue-Liga.
Permite a los usuarios seguir ligas para recibir notificaciones.
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class UsuarioSigueLiga(Base):
    """
    Modelo ORM para la tabla 'usuario_sigue_liga'.

    Relación N:N entre usuarios y ligas que permite a los usuarios
    "seguir" ligas para recibir notificaciones sobre eventos relevantes.

    Attributes:
        id_seguimiento (int): Identificador único del seguimiento (Primary Key)
        id_usuario (int): ID del usuario que sigue (Foreign Key)
        id_liga (int): ID de la liga seguida (Foreign Key)
        created_at (datetime): Fecha y hora de creación del seguimiento
        usuario (Usuario): Relación con el usuario
        liga (Liga): Relación con la liga
    """
    __tablename__ = "usuario_sigue_liga"
    __table_args__ = (
        UniqueConstraint('id_usuario', 'id_liga', name='unique_usuario_liga'),
    )

    # Clave primaria
    id_seguimiento = Column(Integer, primary_key=True)

    # Relaciones
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)

    # Auditoría: fecha de creación
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relaciones ORM
    usuario = relationship("Usuario", lazy="selectin")
    liga = relationship("Liga", lazy="selectin")