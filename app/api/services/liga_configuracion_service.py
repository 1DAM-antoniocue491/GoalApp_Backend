"""
Servicios de lógica de negocio para LigaConfiguracion.
Maneja la configuración específica de cada liga.
"""
from sqlalchemy.orm import Session
from app.models.liga_configuracion import LigaConfiguracion
from app.schemas.liga_configuracion import LigaConfiguracionCreate, LigaConfiguracionUpdate


def obtener_configuracion(db: Session, liga_id: int):
    """
    Obtiene la configuración de una liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        LigaConfiguracion: Configuración de la liga, o None si no existe
    """
    return db.query(LigaConfiguracion).filter(LigaConfiguracion.id_liga == liga_id).first()


def crear_configuracion(db: Session, liga_id: int, datos: LigaConfiguracionCreate):
    """
    Crea la configuración para una liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        datos (LigaConfiguracionCreate): Datos de la configuración

    Returns:
        LigaConfiguracion: Configuración creada

    Raises:
        ValueError: Si ya existe configuración para esta liga
    """
    # Verificar si ya existe configuración
    existente = obtener_configuracion(db, liga_id)
    if existente:
        raise ValueError("La liga ya tiene configuración")

    configuracion = LigaConfiguracion(
        id_liga=liga_id,
        hora_partidos=datos.hora_partidos,
        max_equipos=datos.max_equipos,
        min_jugadores_equipo=datos.min_jugadores_equipo,
        min_partidos_entre_equipos=datos.min_partidos_entre_equipos
    )
    db.add(configuracion)
    db.commit()
    db.refresh(configuracion)
    return configuracion


def actualizar_configuracion(db: Session, liga_id: int, datos: LigaConfiguracionUpdate):
    """
    Actualiza la configuración de una liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        datos (LigaConfiguracionUpdate): Datos a actualizar

    Returns:
        LigaConfiguracion: Configuración actualizada

    Raises:
        ValueError: Si no existe configuración para esta liga
    """
    configuracion = obtener_configuracion(db, liga_id)
    if not configuracion:
        raise ValueError("La liga no tiene configuración")

    # Actualizar solo los campos proporcionados
    if datos.hora_partidos is not None:
        configuracion.hora_partidos = datos.hora_partidos
    if datos.max_equipos is not None:
        configuracion.max_equipos = datos.max_equipos
    if datos.min_jugadores_equipo is not None:
        configuracion.min_jugadores_equipo = datos.min_jugadores_equipo
    if datos.min_partidos_entre_equipos is not None:
        configuracion.min_partidos_entre_equipos = datos.min_partidos_entre_equipos

    db.commit()
    db.refresh(configuracion)
    return configuracion


def crear_configuracion_por_defecto(db: Session, liga_id: int):
    """
    Crea una configuración por defecto para una liga recién creada.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        LigaConfiguracion: Configuración creada con valores por defecto
    """
    configuracion = LigaConfiguracion(id_liga=liga_id)
    db.add(configuracion)
    db.commit()
    db.refresh(configuracion)
    return configuracion