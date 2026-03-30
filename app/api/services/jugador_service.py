"""
Servicios de lógica de negocio para Jugador.
Maneja operaciones CRUD de jugadores, incluyendo su asociación con equipos,
gestión de posiciones, dorsales y estado activo/inactivo.
"""
from sqlalchemy.orm import Session
from app.models.jugador import Jugador
from app.schemas.jugador import JugadorCreate, JugadorUpdate


def crear_jugador(db: Session, datos: JugadorCreate):
    """
    Registra un nuevo jugador en la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (JugadorCreate): Datos del jugador (usuario, equipo, posición, dorsal, activo)
    
    Returns:
        Jugador: Objeto Jugador creado con su ID asignado
    """
    jugador = Jugador(
        id_usuario=datos.id_usuario,
        id_equipo=datos.id_equipo,
        posicion=datos.posicion,
        dorsal=datos.dorsal,
        activo=datos.activo
    )
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    return jugador


def obtener_jugadores(db: Session):
    """
    Obtiene todos los jugadores registrados.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
    
    Returns:
        list[Jugador]: Lista con todos los jugadores
    """
    return db.query(Jugador).all()


def obtener_jugador_por_id(db: Session, jugador_id: int):
    """
    Busca un jugador por su ID.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        jugador_id (int): ID del jugador a buscar
    
    Returns:
        Jugador: Objeto Jugador si existe, None si no se encuentra
    """
    return db.query(Jugador).filter(Jugador.id_jugador == jugador_id).first()


def actualizar_jugador(db: Session, jugador_id: int, datos: JugadorUpdate):
    """
    Actualiza los datos de un jugador existente.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        jugador_id (int): ID del jugador a actualizar
        datos (JugadorUpdate): Datos a actualizar (solo campos proporcionados)
    
    Returns:
        Jugador: Objeto Jugador actualizado
    
    Raises:
        ValueError: Si el jugador no existe
    """
    jugador = obtener_jugador_por_id(db, jugador_id)
    if not jugador:
        raise ValueError("Jugador no encontrado")

    # Actualizar solo los campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(jugador, campo, valor)

    db.commit()
    db.refresh(jugador)
    return jugador


def eliminar_jugador(db: Session, jugador_id: int):
    """
    Elimina un jugador de la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        jugador_id (int): ID del jugador a eliminar
    
    Raises:
        ValueError: Si el jugador no existe
    """
    jugador = obtener_jugador_por_id(db, jugador_id)
    if not jugador:
        raise ValueError("Jugador no encontrado")

    db.delete(jugador)
    db.commit()
