# app/models/liga_configuracion.py
"""
Modelo de Configuración de Liga para gestionar parámetros de cada liga.
Define la configuración específica de cada competición (horarios, límites, etc.).
"""
from sqlalchemy import Column, Integer, Time, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from ..database.connection import Base


class LigaConfiguracion(Base):
    """
    Modelo ORM para la tabla 'liga_configuracion'.

    Almacena la configuración específica de cada liga:
    - Hora habitual de los partidos
    - Número máximo de equipos
    - Mínimo de jugadores por equipo
    - Mínimo de partidos entre equipos

    Attributes:
        id_configuracion (int): Identificador único (Primary Key)
        id_liga (int): ID de la liga (Foreign Key, único)
        hora_partidos (time): Hora habitual de los partidos
        max_equipos (int): Máximo de equipos en la liga
        min_jugadores_equipo (int): Mínimo de jugadores por equipo
        min_partidos_entre_equipos (int): Mínimo de partidos entre equipos
        created_at (datetime): Fecha y hora de creación
        updated_at (datetime): Fecha y hora de última actualización
        liga (Liga): Relación con la liga
    """
    __tablename__ = "liga_configuracion"

    # Clave primaria
    id_configuracion = Column(Integer, primary_key=True, index=True)

    # Relación con liga (única configuración por liga)
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False, unique=True)

    # Configuración de la liga
    hora_partidos = Column(Time, nullable=False, default="17:00:00")
    max_equipos = Column(Integer, nullable=False, default=20)
    min_jugadores_equipo = Column(Integer, nullable=False, default=7)
    min_partidos_entre_equipos = Column(Integer, nullable=False, default=2)

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'), nullable=False)

    # Relaciones ORM
    liga = relationship("Liga", back_populates="configuracion", lazy="selectin")