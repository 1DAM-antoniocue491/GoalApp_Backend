# app/api/services/convocatoria_service.py
"""
Servicios de lógica de negocio para ConvocatoriaPartido.
Maneja operaciones CRUD de convocatorias de jugadores para partidos.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List

from app.models.convocatoria_partido import ConvocatoriaPartido
from app.models.jugador import Jugador
from app.models.partido import Partido
from app.schemas.convocatoria import ConvocatoriaCreate, JugadorConvocadoResponse, ConvocatoriaPartidoResponse


def crear_convocatoria(db: Session, datos: ConvocatoriaCreate) -> List[ConvocatoriaPartido]:
    """
    Crea una convocatoria para un partido.

    Elimina cualquier convocatoria existente y crea una nueva con los jugadores proporcionados.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (ConvocatoriaCreate): Datos de la convocatoria (id_partido, lista de jugadores)

    Returns:
        List[ConvocatoriaPartido]: Lista de convocatorias creadas

    Raises:
        ValueError: Si el partido no existe, está iniciado o hay más de 11 titulares
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == datos.id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el partido no está iniciado o finalizado
    if partido.estado in ["En Juego", "Finalizado"]:
        raise ValueError(f"No se puede modificar convocatoria de partido {partido.estado.lower()}")

    # Contar titulares
    titulares = sum(1 for j in datos.jugadores if j.es_titular)
    if titulares > 11:
        raise ValueError("No puede haber más de 11 titulares")

    # Eliminar convocatoria existente
    db.query(ConvocatoriaPartido).filter(
        ConvocatoriaPartido.id_partido == datos.id_partido
    ).delete()

    # Crear nueva convocatoria
    convocatorias = []
    for jugador_data in datos.jugadores:
        convocatoria = ConvocatoriaPartido(
            id_partido=datos.id_partido,
            id_jugador=jugador_data.id_jugador,
            es_titular=jugador_data.es_titular
        )
        db.add(convocatoria)
        convocatorias.append(convocatoria)

    db.commit()

    for c in convocatorias:
        db.refresh(c)

    return convocatorias


def obtener_convocatoria_partido(db: Session, id_partido: int) -> ConvocatoriaPartidoResponse | None:
    """
    Obtiene la convocatoria completa de un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_partido (int): ID del partido

    Returns:
        ConvocatoriaPartidoResponse: Convocatoria con titulares y suplentes

    Raises:
        ValueError: Si el partido no existe
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Obtener convocatorias con jugadores y usuarios cargados (usar joinedload para evitar lazy='raise')
    from sqlalchemy.orm import joinedload

    convocatorias = db.query(ConvocatoriaPartido).options(
        joinedload(ConvocatoriaPartido.jugador).joinedload(Jugador.usuario)
    ).filter(
        ConvocatoriaPartido.id_partido == id_partido
    ).all()

    # Construir respuesta con información de jugadores
    titulares = []
    suplentes = []

    for conv in convocatorias:
        # Ahora conv.jugador está cargado gracias a joinedload
        jugador = conv.jugador
        if jugador:
            jugador_response = JugadorConvocadoResponse(
                id_jugador=jugador.id_jugador,
                nombre=jugador.usuario.nombre,
                dorsal=jugador.dorsal,
                posicion=jugador.posicion,
                es_titular=conv.es_titular
            )
            if conv.es_titular:
                titulares.append(jugador_response)
            else:
                suplentes.append(jugador_response)

    return ConvocatoriaPartidoResponse(
        id_partido=id_partido,
        titulares=titulares,
        suplentes=suplentes
    )


def obtener_convocatoria_equipo(db: Session, id_partido: int, id_equipo: int) -> ConvocatoriaPartidoResponse | None:
    """
    Obtiene la convocatoria de un equipo específico para un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_partido (int): ID del partido
        id_equipo (int): ID del equipo

    Returns:
        ConvocatoriaPartidoResponse: Convocatoria con titulares y suplentes del equipo

    Raises:
        ValueError: Si el partido o equipo no existe
    """
    from app.models.equipo import Equipo
    from app.models.usuario import Usuario

    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el equipo es local o visitante
    if partido.id_equipo_local != id_equipo and partido.id_equipo_visitante != id_equipo:
        raise ValueError("El equipo no participa en este partido")

    # Obtener convocatorias con joinedload para evitar lazy='raise'
    from sqlalchemy.orm import joinedload

    convocatorias = db.query(ConvocatoriaPartido).options(
        joinedload(ConvocatoriaPartido.jugador).joinedload(Jugador.usuario)
    ).join(
        Jugador, ConvocatoriaPartido.id_jugador == Jugador.id_jugador
    ).filter(
        and_(
            ConvocatoriaPartido.id_partido == id_partido,
            Jugador.id_equipo == id_equipo
        )
    ).all()

    # Construir respuesta
    titulares = []
    suplentes = []

    for conv in convocatorias:
        jugador = conv.jugador
        if jugador:
            jugador_response = JugadorConvocadoResponse(
                id_jugador=jugador.id_jugador,
                nombre=jugador.usuario.nombre,
                dorsal=jugador.dorsal,
                posicion=jugador.posicion,
                es_titular=conv.es_titular
            )
            if conv.es_titular:
                titulares.append(jugador_response)
            else:
                suplentes.append(jugador_response)

    return ConvocatoriaPartidoResponse(
        id_partido=id_partido,
        titulares=titulares,
        suplentes=suplentes
    )


def eliminar_convocatoria(db: Session, id_partido: int) -> bool:
    """
    Elimina la convocatoria de un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_partido (int): ID del partido

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si el partido no existe o está iniciado
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el partido no está iniciado o finalizado
    if partido.estado in ["En Juego", "Finalizado"]:
        raise ValueError(f"No se puede modificar convocatoria de partido {partido.estado.lower()}")

    # Eliminar convocatoria
    db.query(ConvocatoriaPartido).filter(
        ConvocatoriaPartido.id_partido == id_partido
    ).delete()
    db.commit()

    return True