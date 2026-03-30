"""
Servicios de lógica de negocio para Equipo.
Maneja operaciones CRUD de equipos de fútbol, incluyendo gestión de datos,
asociaciones con liga, entrenador y delegado.
"""
from sqlalchemy.orm import Session
from app.models.equipo import Equipo
from app.schemas.equipo import EquipoCreate, EquipoUpdate


def crear_equipo(db: Session, datos: EquipoCreate):
    """
    Crea un nuevo equipo en la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (EquipoCreate): Datos del equipo a crear (nombre, escudo, colores, IDs)
    
    Returns:
        Equipo: Objeto Equipo creado con su ID asignado
    """
    equipo = Equipo(
        nombre=datos.nombre,
        escudo=datos.escudo,
        colores=datos.colores,
        id_liga=datos.id_liga,
        id_entrenador=datos.id_entrenador,
        id_delegado=datos.id_delegado
    )
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo


def obtener_equipos(db: Session):
    """
    Obtiene todos los equipos registrados.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
    
    Returns:
        list[Equipo]: Lista con todos los equipos
    """
    return db.query(Equipo).all()


def obtener_equipo_por_id(db: Session, equipo_id: int):
    """
    Busca un equipo por su ID.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo a buscar
    
    Returns:
        Equipo: Objeto Equipo si existe, None si no se encuentra
    """
    return db.query(Equipo).filter(Equipo.id_equipo == equipo_id).first()


def actualizar_equipo(db: Session, equipo_id: int, datos: EquipoUpdate):
    """
    Actualiza los datos de un equipo existente.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo a actualizar
        datos (EquipoUpdate): Datos a actualizar (solo campos proporcionados)
    
    Returns:
        Equipo: Objeto Equipo actualizado
    
    Raises:
        ValueError: Si el equipo no existe
    """
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise ValueError("Equipo no encontrado")

    # Actualizar solo los campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(equipo, campo, valor)

    db.commit()
    db.refresh(equipo)
    return equipo


def eliminar_equipo(db: Session, equipo_id: int):
    """
    Elimina un equipo de la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo a eliminar
    
    Raises:
        ValueError: Si el equipo no existe
    """
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise ValueError("Equipo no encontrado")

    db.delete(equipo)
    db.commit()
