# app/models/equipo.py
"""
Modelo de Equipo para gestionar los equipos de la liga.
Incluye información del equipo, entrenador y delegado.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Equipo(Base):
    """
    Modelo ORM para la tabla 'equipos'.

    Representa un equipo participante en una liga con su información básica,
    pertenencia a una liga, y referencias a su entrenador y delegado.

    Attributes:
        id_equipo (int): Identificador único del equipo (Primary Key)
        nombre (str): Nombre del equipo (máx. 100 caracteres, único)
        escudo (str): URL o path del escudo del equipo (opcional, máx. 255 caracteres)
        colores (str): Colores del equipo (opcional, máx. 50 caracteres)
        id_liga (int): ID de la liga a la que pertenece (Foreign Key)
        id_entrenador (int): ID del usuario que es entrenador (Foreign Key)
        id_delegado (int): ID del usuario que es delegado (Foreign Key)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        liga (Liga): Relación con la liga
        entrenador (Usuario): Relación con el usuario entrenador
        delegado (Usuario): Relación con el usuario delegado
    """
    __tablename__ = "equipos"

    # Clave primaria
    id_equipo = Column(Integer, primary_key=True, index=True)

    # Información básica del equipo
    nombre = Column(String(100), nullable=False, unique=True)  # Nombre único del equipo
    escudo = Column(String(255), nullable=True)  # URL o path del escudo (opcional)
    colores = Column(String(50), nullable=True)  # Ejemplo: "Azul y Blanco"

    # Relaciones: liga, entrenador y delegado
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)
    id_entrenador = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_delegado = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    liga = relationship("Liga", back_populates="equipos", lazy="selectin")
    entrenador = relationship("Usuario", foreign_keys=[id_entrenador], lazy="selectin")
    delegado = relationship("Usuario", foreign_keys=[id_delegado], lazy="selectin")
