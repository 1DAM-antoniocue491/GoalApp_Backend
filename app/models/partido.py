# app/models/partido.py
"""
Modelo de Partido para gestionar los encuentros entre equipos.
Almacena fecha, equipos, resultado y estado del partido.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class Partido(Base):
    """
    Modelo ORM para la tabla 'partidos'.

    Representa un partido de fútbol entre dos equipos en una liga específica.
    Incluye información de fecha, estado del partido y resultado.

    Attributes:
        id_partido (int): Identificador único del partido (Primary Key)
        id_liga (int): ID de la liga a la que pertenece (Foreign Key)
        id_equipo_local (int): ID del equipo que juega como local (Foreign Key)
        id_equipo_visitante (int): ID del equipo visitante (Foreign Key)
        fecha (datetime): Fecha y hora programada del partido
        estado (str): Estado del partido (ej: "Programado", "En curso", "Finalizado", máx. 50 caracteres)
        goles_local (int): Goles marcados por el equipo local (opcional, null si no ha comenzado)
        goles_visitante (int): Goles marcados por el equipo visitante (opcional, null si no ha comenzado)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        liga (Liga): Relación con la liga
        equipo_local (Equipo): Relación con el equipo local
        equipo_visitante (Equipo): Relación con el equipo visitante
    """
    __tablename__ = "partidos"

    # Clave primaria
    id_partido = Column(Integer, primary_key=True)

    # Relaciones: liga y equipos participantes
    id_liga = Column(Integer, ForeignKey("ligas.id_liga"), nullable=False)
    id_equipo_local = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)
    id_equipo_visitante = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)

    # Información del partido
    fecha = Column(DateTime(timezone=True), nullable=False)  # Fecha y hora del partido
    estado = Column(String(50), nullable=False)  # Ejemplo: "Programado", "En curso", "Finalizado", "Suspendido"

    # Resultado del partido (null si no ha comenzado o está en curso)
    goles_local = Column(Integer, nullable=True)  # Goles del equipo local
    goles_visitante = Column(Integer, nullable=True)  # Goles del equipo visitante

    # Auditoría: fechas de creación y actualización
    # default=func.now() ensures consistent timestamps across all database backends
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    liga = relationship("Liga", lazy="raise")
    equipo_local = relationship("Equipo", foreign_keys=[id_equipo_local], lazy="raise")
    equipo_visitante = relationship("Equipo", foreign_keys=[id_equipo_visitante], lazy="raise")
