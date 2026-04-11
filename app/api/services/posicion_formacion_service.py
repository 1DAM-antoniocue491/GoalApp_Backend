# app/api/services/posicion_formacion_service.py
"""
Servicios de lógica de negocio para PosicionFormacion.
Maneja operaciones CRUD de las posiciones genéricas del campo de fútbol.
"""
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.posicion_formacion import PosicionFormacion
from app.schemas.posicion_formacion import PosicionFormacionCreate, PosicionFormacionUpdate


def crear_posicion_formacion(db: Session, datos: PosicionFormacionCreate) -> PosicionFormacion:
    """
    Crea una nueva posición de formación.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (PosicionFormacionCreate): Datos de la posición (nombre, descripcion)

    Returns:
        PosicionFormacion: Objeto PosicionFormacion creado con su ID asignado

    Raises:
        ValueError: Si ya existe una posición con el mismo nombre
    """
    # Verificar si ya existe una posición con el mismo nombre
    posicion_existente = db.query(PosicionFormacion).filter(
        PosicionFormacion.nombre == datos.nombre
    ).first()

    if posicion_existente:
        raise ValueError(f"Ya existe una posición con el nombre '{datos.nombre}'")

    posicion = PosicionFormacion(
        nombre=datos.nombre,
        descripcion=datos.descripcion
    )
    db.add(posicion)
    db.commit()
    db.refresh(posicion)
    return posicion


def obtener_posiciones_formacion(db: Session) -> List[PosicionFormacion]:
    """
    Obtiene todas las posiciones de formación registradas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        List[PosicionFormacion]: Lista con todas las posiciones
    """
    return db.query(PosicionFormacion).order_by(PosicionFormacion.nombre).all()


def obtener_posicion_formacion_por_id(db: Session, id_posicion: int) -> Optional[PosicionFormacion]:
    """
    Busca una posición de formación por su ID.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_posicion (int): ID de la posición a buscar

    Returns:
        PosicionFormacion | None: Objeto PosicionFormacion si existe, None si no se encuentra
    """
    return db.query(PosicionFormacion).filter(PosicionFormacion.id_posicion == id_posicion).first()


def actualizar_posicion_formacion(
    db: Session,
    id_posicion: int,
    datos: PosicionFormacionUpdate
) -> PosicionFormacion:
    """
    Actualiza los datos de una posición de formación existente.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_posicion (int): ID de la posición a actualizar
        datos (PosicionFormacionUpdate): Datos a actualizar (nombre, descripcion)

    Returns:
        PosicionFormacion: Objeto PosicionFormacion actualizado

    Raises:
        ValueError: Si la posición no existe o si el nombre ya está en uso
    """
    posicion = obtener_posicion_formacion_por_id(db, id_posicion)
    if not posicion:
        raise ValueError(f"Posición con ID {id_posicion} no encontrada")

    # Actualizar nombre si se proporciona
    if datos.nombre is not None:
        # Verificar que el nombre no esté en uso por otra posición
        posicion_existente = db.query(PosicionFormacion).filter(
            PosicionFormacion.nombre == datos.nombre,
            PosicionFormacion.id_posicion != id_posicion
        ).first()
        if posicion_existente:
            raise ValueError(f"Ya existe otra posición con el nombre '{datos.nombre}'")
        posicion.nombre = datos.nombre

    # Actualizar descripción si se proporciona
    if datos.descripcion is not None:
        posicion.descripcion = datos.descripcion

    db.commit()
    db.refresh(posicion)
    return posicion


def eliminar_posicion_formacion(db: Session, id_posicion: int) -> bool:
    """
    Elimina una posición de formación de la base de datos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_posicion (int): ID de la posición a eliminar

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si la posición no existe
    """
    posicion = obtener_posicion_formacion_por_id(db, id_posicion)
    if not posicion:
        raise ValueError(f"Posición con ID {id_posicion} no encontrada")

    db.delete(posicion)
    db.commit()
    return True