"""
Servicios de lógica de negocio para Partido.
Maneja operaciones CRUD de partidos, incluyendo gestión de equipos local y visitante,
marcadores, fechas y estados del partido.
"""
from sqlalchemy.orm import Session
from app.models.partido import Partido
from app.schemas.partido import PartidoCreate, PartidoUpdate


def crear_partido(db: Session, datos: PartidoCreate):
    """
    Crea un nuevo partido en la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (PartidoCreate): Datos del partido (liga, equipos, fecha, estado, goles)
    
    Returns:
        Partido: Objeto Partido creado con su ID asignado
    """
    partido = Partido(
        id_liga=datos.id_liga,
        id_equipo_local=datos.id_equipo_local,
        id_equipo_visitante=datos.id_equipo_visitante,
        fecha=datos.fecha,
        estado=datos.estado,
        goles_local=datos.goles_local,
        goles_visitante=datos.goles_visitante
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    return partido


def obtener_partidos(db: Session):
    """
    Obtiene todos los partidos registrados.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
    
    Returns:
        list[Partido]: Lista con todos los partidos
    """
    return db.query(Partido).all()


def obtener_partido_por_id(db: Session, partido_id: int):
    """
    Busca un partido por su ID.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a buscar
    
    Returns:
        Partido: Objeto Partido si existe, None si no se encuentra
    """
    return db.query(Partido).filter(Partido.id_partido == partido_id).first()


def actualizar_partido(db: Session, partido_id: int, datos: PartidoUpdate):
    """
    Actualiza los datos de un partido existente.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a actualizar
        datos (PartidoUpdate): Datos a actualizar (solo campos proporcionados)
    
    Returns:
        Partido: Objeto Partido actualizado
    
    Raises:
        ValueError: Si el partido no existe
    """
    partido = obtener_partido_por_id(db, partido_id)
    if not partido:
        raise ValueError("Partido no encontrado")

    # Actualizar solo los campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(partido, campo, valor)

    db.commit()
    db.refresh(partido)
    return partido


def eliminar_partido(db: Session, partido_id: int):
    """
    Elimina un partido de la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a eliminar
    
    Raises:
        ValueError: Si el partido no existe
    """
    partido = obtener_partido_por_id(db, partido_id)
    if not partido:
        raise ValueError("Partido no encontrado")

    db.delete(partido)
    db.commit()
