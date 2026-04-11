# app/api/services/alineacion_service.py
"""
Servicios de lógica de negocio para AlineacionPartido.
Maneja operaciones CRUD de alineaciones de jugadores en partidos.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from app.models.alineacion_partido import AlineacionPartido
from app.models.jugador import Jugador
from app.models.partido import Partido
from app.models.posicion_formacion import PosicionFormacion
from app.models.equipo import Equipo
from app.schemas.alineacion import (
    AlineacionCreate,
    AlineacionUpdate,
    AlineacionBulkCreate,
    JugadorAlineadoResponse,
    AlineacionEquipoResponse
)


def crear_alineacion(db: Session, datos: AlineacionCreate) -> AlineacionPartido:
    """
    Crea una alineación individual para un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (AlineacionCreate): Datos de la alineación

    Returns:
        AlineacionPartido: Objeto AlineacionPartido creado

    Raises:
        ValueError: Si el partido, jugador o posición no existen
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == datos.id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el jugador existe
    jugador = db.query(Jugador).filter(Jugador.id_jugador == datos.id_jugador).first()
    if not jugador:
        raise ValueError("Jugador no encontrado")

    # Verificar que la posición existe
    posicion = db.query(PosicionFormacion).filter(
        PosicionFormacion.id_posicion == datos.id_posicion
    ).first()
    if not posicion:
        raise ValueError("Posición no encontrada")

    # Verificar que el jugador no esté ya alineado en este partido
    alineacion_existente = db.query(AlineacionPartido).filter(
        and_(
            AlineacionPartido.id_partido == datos.id_partido,
            AlineacionPartido.id_jugador == datos.id_jugador
        )
    ).first()

    if alineacion_existente:
        raise ValueError("El jugador ya está alineado en este partido")

    alineacion = AlineacionPartido(
        id_partido=datos.id_partido,
        id_jugador=datos.id_jugador,
        id_posicion=datos.id_posicion,
        titular=datos.titular
    )
    db.add(alineacion)
    db.commit()
    db.refresh(alineacion)
    return alineacion


def crear_alineaciones_bulk(db: Session, datos: AlineacionBulkCreate) -> List[AlineacionPartido]:
    """
    Crea múltiples alineaciones para un partido en una sola operación.
    Elimina alineaciones existentes antes de crear las nuevas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (AlineacionBulkCreate): Datos de las alineaciones (id_partido + lista)

    Returns:
        List[AlineacionPartido]: Lista de alineaciones creadas

    Raises:
        ValueError: Si el partido no existe o si hay errores en las alineaciones
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == datos.id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Contar titulares
    titulares = sum(1 for a in datos.alineaciones if a.titular)
    if titulares > 11:
        raise ValueError("No puede haber más de 11 titulares por equipo")

    # Eliminar alineaciones existentes del partido
    db.query(AlineacionPartido).filter(
        AlineacionPartido.id_partido == datos.id_partido
    ).delete()

    # Crear nuevas alineaciones
    alineaciones_creadas = []
    for alineacion_data in datos.alineaciones:
        # Verificar que el jugador existe
        jugador = db.query(Jugador).filter(Jugador.id_jugador == alineacion_data.id_jugador).first()
        if not jugador:
            raise ValueError(f"Jugador con ID {alineacion_data.id_jugador} no encontrado")

        # Verificar que la posición existe
        posicion = db.query(PosicionFormacion).filter(
            PosicionFormacion.id_posicion == alineacion_data.id_posicion
        ).first()
        if not posicion:
            raise ValueError(f"Posición con ID {alineacion_data.id_posicion} no encontrada")

        alineacion = AlineacionPartido(
            id_partido=datos.id_partido,
            id_jugador=alineacion_data.id_jugador,
            id_posicion=alineacion_data.id_posicion,
            titular=alineacion_data.titular
        )
        db.add(alineacion)
        alineaciones_creadas.append(alineacion)

    db.commit()

    for a in alineaciones_creadas:
        db.refresh(a)

    return alineaciones_creadas


def obtener_alineacion_por_id(db: Session, id_alineacion: int) -> AlineacionPartido | None:
    """
    Obtiene una alineación por su ID.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_alineacion (int): ID de la alineación

    Returns:
        AlineacionPartido | None: La alineación si existe, None si no
    """
    return db.query(AlineacionPartido).filter(
        AlineacionPartido.id_alineacion == id_alineacion
    ).first()


def obtener_alineaciones_partido(db: Session, id_partido: int) -> List[AlineacionPartido]:
    """
    Obtiene todas las alineaciones de un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_partido (int): ID del partido

    Returns:
        List[AlineacionPartido]: Lista de alineaciones del partido

    Raises:
        ValueError: Si el partido no existe
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    return db.query(AlineacionPartido).filter(
        AlineacionPartido.id_partido == id_partido
    ).all()


def obtener_alineacion_equipo(
    db: Session,
    id_partido: int,
    id_equipo: int
) -> AlineacionEquipoResponse:
    """
    Obtiene la alineación de un equipo específico en un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_partido (int): ID del partido
        id_equipo (int): ID del equipo

    Returns:
        AlineacionEquipoResponse: Alineación del equipo con titulares y suplentes

    Raises:
        ValueError: Si el partido o equipo no existen, o si el equipo no participa
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el equipo es local o visitante
    if partido.id_equipo_local != id_equipo and partido.id_equipo_visitante != id_equipo:
        raise ValueError("El equipo no participa en este partido")

    # Obtener nombre del equipo
    equipo = db.query(Equipo).filter(Equipo.id_equipo == id_equipo).first()
    nombre_equipo = equipo.nombre if equipo else ""

    # Obtener alineaciones del equipo en este partido
    alineaciones = db.query(AlineacionPartido).join(Jugador).filter(
        and_(
            AlineacionPartido.id_partido == id_partido,
            Jugador.id_equipo == id_equipo
        )
    ).all()

    # Construir respuesta
    titulares = []
    suplentes = []

    for alineacion in alineaciones:
        jugador = db.query(Jugador).filter(Jugador.id_jugador == alineacion.id_jugador).first()
        posicion = db.query(PosicionFormacion).filter(
            PosicionFormacion.id_posicion == alineacion.id_posicion
        ).first()

        if jugador and posicion:
            jugador_response = JugadorAlineadoResponse(
                id_alineacion=alineacion.id_alineacion,
                id_jugador=jugador.id_jugador,
                nombre=jugador.usuario.nombre,
                dorsal=jugador.dorsal,
                posicion_jugador=jugador.posicion,
                posicion_campo=posicion.nombre,
                id_posicion=alineacion.id_posicion,
                titular=alineacion.titular
            )
            if alineacion.titular:
                titulares.append(jugador_response)
            else:
                suplentes.append(jugador_response)

    return AlineacionEquipoResponse(
        id_partido=id_partido,
        id_equipo=id_equipo,
        nombre_equipo=nombre_equipo,
        titulares=titulares,
        suplentes=suplentes
    )


def actualizar_alineacion(
    db: Session,
    id_alineacion: int,
    datos: AlineacionUpdate
) -> AlineacionPartido:
    """
    Actualiza una alineación existente.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_alineacion (int): ID de la alineación a actualizar
        datos (AlineacionUpdate): Datos a actualizar

    Returns:
        AlineacionPartido: Alineación actualizada

    Raises:
        ValueError: Si la alineación no existe o la posición no existe
    """
    alineacion = obtener_alineacion_por_id(db, id_alineacion)
    if not alineacion:
        raise ValueError(f"Alineación con ID {id_alineacion} no encontrada")

    # Actualizar posición si se proporciona
    if datos.id_posicion is not None:
        posicion = db.query(PosicionFormacion).filter(
            PosicionFormacion.id_posicion == datos.id_posicion
        ).first()
        if not posicion:
            raise ValueError(f"Posición con ID {datos.id_posicion} no encontrada")
        alineacion.id_posicion = datos.id_posicion

    # Actualizar estado de titular si se proporciona
    if datos.titular is not None:
        alineacion.titular = datos.titular

    db.commit()
    db.refresh(alineacion)
    return alineacion


def eliminar_alineacion(db: Session, id_alineacion: int) -> bool:
    """
    Elimina una alineación de la base de datos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_alineacion (int): ID de la alineación a eliminar

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si la alineación no existe
    """
    alineacion = obtener_alineacion_por_id(db, id_alineacion)
    if not alineacion:
        raise ValueError(f"Alineación con ID {id_alineacion} no encontrada")

    db.delete(alineacion)
    db.commit()
    return True


def eliminar_alineaciones_partido(db: Session, id_partido: int) -> bool:
    """
    Elimina todas las alineaciones de un partido.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_partido (int): ID del partido

    Returns:
        bool: True si se eliminaron correctamente

    Raises:
        ValueError: Si el partido no existe
    """
    # Verificar que el partido existe
    partido = db.query(Partido).filter(Partido.id_partido == id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    db.query(AlineacionPartido).filter(
        AlineacionPartido.id_partido == id_partido
    ).delete()
    db.commit()
    return True