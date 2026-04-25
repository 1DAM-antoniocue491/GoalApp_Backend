# app/models/estado_jugador_partido.py
"""
Modelo de Estado de Jugador por Partido para trackear quién está jugando vs suplente.
Permite validar sustituciones y actualizar el estado en tiempo real.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.connection import Base


class EstadoJugadorPartido(Base):
    """
    Modelo ORM para la tabla 'estado_jugador_partido'.

    Trackea el estado de cada jugador durante un partido específico,
    permitiendo validar sustituciones y consultar quién está en el campo.

    Attributes:
        id_estado (int): Identificador único del estado (Primary Key)
        id_partido (int): ID del partido (Foreign Key)
        id_jugador (int): ID del jugador (Foreign Key)
        id_equipo (int): ID del equipo (Foreign Key)
        estado (str): 'jugando' | 'suplente' | 'lesionado' | 'expulsado'
        minuto_entrada (int): Minuto cuando entró al campo (null si empezó jugando)
        minuto_salida (int): Minuto cuando salió del campo (null si sigue jugando)
        created_at (datetime): Fecha de creación del registro
        updated_at (datetime): Fecha de última actualización

    Ejemplo de uso:
        - Al iniciar partido: once inicial = 'jugando', resto = 'suplente'
        - Al registrar sustitución:
            - Jugador que entra: 'suplente' → 'jugando'
            - Jugador que sale: 'jugando' → 'suplente'
    """
    __tablename__ = "estado_jugador_partido"

    # Clave primaria
    id_estado = Column(Integer, primary_key=True)

    # Relaciones: partido, jugador y equipo
    id_partido = Column(Integer, ForeignKey("partidos.id_partido"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("jugadores.id_jugador"), nullable=False)
    id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"), nullable=False)

    # Estado actual del jugador
    estado = Column(String(20), nullable=False, default="suplente")  # 'jugando', 'suplente', 'lesionado', 'expulsado'

    # Minutos de entrada/salida (para tracking histórico)
    minuto_entrada = Column(Integer, nullable=True)  # Minuto cuando entró al campo
    minuto_salida = Column(Integer, nullable=True)   # Minuto cuando salió del campo

    # Auditoría: fechas de creación y actualización
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    partido = relationship("Partido", back_populates="estados_jugadores", lazy="raise")
    jugador = relationship("Jugador", back_populates="estados_partido", lazy="raise")
    equipo = relationship("Equipo", back_populates="estados_jugadores_partido", lazy="raise")
