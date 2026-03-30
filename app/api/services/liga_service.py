"""
Servicios de lógica de negocio para Liga.
Maneja operaciones CRUD de ligas/competiciones, incluyendo gestión de
nombres y temporadas.
"""
from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict

from app.models.liga import Liga
from app.models.liga_configuracion import LigaConfiguracion
from app.models.equipo import Equipo
from app.models.partido import Partido
from app.schemas.liga import LigaCreate, LigaUpdate
from app.schemas.clasificacion import ClasificacionItem


def crear_liga(db: Session, datos: LigaCreate):
    """
    Crea una nueva liga en la base de datos y su configuración por defecto.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (LigaCreate): Datos de la liga (nombre y temporada)

    Returns:
        Liga: Objeto Liga creado con su ID asignado
    """
    liga = Liga(
        nombre=datos.nombre,
        temporada=datos.temporada
    )
    db.add(liga)
    db.flush()  # Obtener el ID de la liga sin hacer commit

    # Crear configuración por defecto
    configuracion = LigaConfiguracion(id_liga=liga.id_liga)
    db.add(configuracion)

    db.commit()
    db.refresh(liga)
    return liga


def obtener_ligas(db: Session):
    """
    Obtiene todas las ligas registradas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        list[Liga]: Lista con todas las ligas
    """
    return db.query(Liga).all()


def obtener_liga_por_id(db: Session, liga_id: int):
    """
    Busca una liga por su ID.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a buscar

    Returns:
        Liga: Objeto Liga si existe, None si no se encuentra
    """
    return db.query(Liga).filter(Liga.id_liga == liga_id).first()


def actualizar_liga(db: Session, liga_id: int, datos: LigaUpdate):
    """
    Actualiza los datos de una liga existente.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a actualizar
        datos (LigaUpdate): Datos a actualizar (nombre, temporada y/o activa)

    Returns:
        Liga: Objeto Liga actualizado

    Raises:
        ValueError: Si la liga no existe
    """
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    # Actualizar nombre si se proporciona
    if datos.nombre is not None:
        liga.nombre = datos.nombre
    # Actualizar temporada si se proporciona
    if datos.temporada is not None:
        liga.temporada = datos.temporada
    # Actualizar estado activa si se proporciona
    if datos.activa is not None:
        liga.activa = datos.activa

    db.commit()
    db.refresh(liga)
    return liga


def reactivar_liga(db: Session, liga_id: int) -> Liga:
    """
    Reactiva una liga que estaba inactiva.

    Solo permite reactivar si la liga está inactiva.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a reactivar

    Returns:
        Liga: Objeto Liga reactivado

    Raises:
        ValueError: Si la liga no existe o ya está activa
    """
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    if liga.activa:
        raise ValueError("La liga ya está activa")

    liga.activa = True
    db.commit()
    db.refresh(liga)
    return liga


def desactivar_liga(db: Session, liga_id: int) -> Liga:
    """
    Desactiva una liga (la marca como inactiva).

    Solo permite desactivar si la liga está activa.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a desactivar

    Returns:
        Liga: Objeto Liga desactivado

    Raises:
        ValueError: Si la liga no existe o ya está inactiva
    """
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    if not liga.activa:
        raise ValueError("La liga ya está inactiva")

    liga.activa = False
    db.commit()
    db.refresh(liga)
    return liga


def eliminar_liga(db: Session, liga_id: int):
    """
    Elimina una liga de la base de datos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a eliminar

    Raises:
        ValueError: Si la liga no existe
    """
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    db.delete(liga)
    db.commit()


def obtener_clasificacion(db: Session, liga_id: int) -> List[ClasificacionItem]:
    """
    Calcula la clasificación de una liga.

    Obtiene todos los partidos finalizados de la liga y calcula
    las estadísticas de cada equipo (puntos, victorias, empates, derrotas, goles).

    Ordenamiento:
    1. Puntos (descendente)
    2. Diferencia de goles (descendente)
    3. Goles a favor (descendente)

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        List[ClasificacionItem]: Lista de equipos ordenados por clasificación

    Raises:
        ValueError: Si la liga no existe
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    # Obtener equipos de la liga
    equipos = db.query(Equipo).filter(Equipo.id_liga == liga_id).all()

    # Obtener partidos finalizados de la liga
    partidos = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado == "finalizado",
        Partido.goles_local.isnot(None),
        Partido.goles_visitante.isnot(None)
    ).all()

    # Diccionario para almacenar estadísticas por equipo
    stats = defaultdict(lambda: {
        "id_equipo": 0,
        "nombre_equipo": "",
        "puntos": 0,
        "partidos_jugados": 0,
        "victorias": 0,
        "empates": 0,
        "derrotas": 0,
        "goles_favor": 0,
        "goles_contra": 0
    })

    # Inicializar equipos
    for equipo in equipos:
        stats[equipo.id_equipo]["id_equipo"] = equipo.id_equipo
        stats[equipo.id_equipo]["nombre_equipo"] = equipo.nombre

    # Calcular estadísticas a partir de los partidos
    for partido in partidos:
        id_local = partido.id_equipo_local
        id_visitante = partido.id_equipo_visitante
        goles_local = partido.goles_local
        goles_visitante = partido.goles_visitante

        # Actualizar estadísticas del equipo local
        stats[id_local]["partidos_jugados"] += 1
        stats[id_local]["goles_favor"] += goles_local
        stats[id_local]["goles_contra"] += goles_visitante

        # Actualizar estadísticas del equipo visitante
        stats[id_visitante]["partidos_jugados"] += 1
        stats[id_visitante]["goles_favor"] += goles_visitante
        stats[id_visitante]["goles_contra"] += goles_local

        # Determinar resultado y asignar puntos
        if goles_local > goles_visitante:
            # Victoria local
            stats[id_local]["victorias"] += 1
            stats[id_local]["puntos"] += 3
            stats[id_visitante]["derrotas"] += 1
        elif goles_local < goles_visitante:
            # Victoria visitante
            stats[id_visitante]["victorias"] += 1
            stats[id_visitante]["puntos"] += 3
            stats[id_local]["derrotas"] += 1
        else:
            # Empate
            stats[id_local]["empates"] += 1
            stats[id_local]["puntos"] += 1
            stats[id_visitante]["empates"] += 1
            stats[id_visitante]["puntos"] += 1

    # Convertir a lista y calcular diferencia de goles
    clasificacion = []
    for equipo_stats in stats.values():
        equipo_stats["diferencia_goles"] = equipo_stats["goles_favor"] - equipo_stats["goles_contra"]
        clasificacion.append(equipo_stats)

    # Ordenar: puntos DESC, diferencia_goles DESC, goles_favor DESC
    clasificacion.sort(
        key=lambda x: (x["puntos"], x["diferencia_goles"], x["goles_favor"]),
        reverse=True
    )

    # Asignar posiciones y crear objetos de respuesta
    resultado = []
    for posicion, equipo in enumerate(clasificacion, start=1):
        resultado.append(ClasificacionItem(
            posicion=posicion,
            id_equipo=equipo["id_equipo"],
            nombre_equipo=equipo["nombre_equipo"],
            puntos=equipo["puntos"],
            partidos_jugados=equipo["partidos_jugados"],
            victorias=equipo["victorias"],
            empates=equipo["empates"],
            derrotas=equipo["derrotas"],
            goles_favor=equipo["goles_favor"],
            goles_contra=equipo["goles_contra"],
            diferencia_goles=equipo["diferencia_goles"]
        ))

    return resultado
