"""
Servicios de lógica de negocio para Equipo.
Maneja operaciones CRUD de equipos de fútbol, incluyendo gestión de datos,
asociaciones con liga, entrenador y delegado.
"""
from sqlalchemy.orm import Session
from app.models.equipo import Equipo
from app.models.partido import Partido
from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoRendimientoResponse


def crear_equipo(db: Session, datos: EquipoCreate, usuario_id: int = None):
    """
    Crea un nuevo equipo en la base de datos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (EquipoCreate): Datos del equipo a crear (nombre, escudo, colores, IDs)
        usuario_id (int, optional): ID del usuario que crea el equipo. Se usa como
                                    entrenador y delegado por defecto si no se especifican.

    Returns:
        Equipo: Objeto Equipo creado con su ID asignado
    """
    # Si no se especifica entrenador/delegado, usar el usuario que crea el equipo
    id_entrenador = datos.id_entrenador or usuario_id
    id_delegado = datos.id_delegado or usuario_id

    equipo = Equipo(
        nombre=datos.nombre,
        escudo=datos.escudo,
        colores=datos.colores,
        id_liga=datos.id_liga,
        id_entrenador=id_entrenador,
        id_delegado=id_delegado
    )
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo


def obtener_equipos(db: Session, liga_id: int = None):
    """
    Obtiene todos los equipos registrados, opcionalmente filtrados por liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int, optional): ID de la liga para filtrar

    Returns:
        list[Equipo]: Lista con todos los equipos (filtrados por liga si se proporciona)
    """
    query = db.query(Equipo)
    if liga_id is not None:
        query = query.filter(Equipo.id_liga == liga_id)
    return query.all()


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


def obtener_equipos_con_rendimiento(db: Session, liga_id: int):
    """
    Obtiene todos los equipos de una liga con sus estadísticas de rendimiento.

    Calcula victorias, empates y derrotas de cada equipo basándose en los partidos
    finalizados de la liga especificada.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga para filtrar los equipos

    Returns:
        list[EquipoRendimientoResponse]: Lista de equipos con sus estadísticas de rendimiento.
                                          Cada equipo incluye:
                                          - id_equipo, nombre, escudo, colores, id_liga
                                          - partidos_jugados, victorias, empates, derrotas
                                          - porcentaje_victorias (0-100)
    """
    # Obtener todos los equipos de la liga
    equipos = db.query(Equipo).filter(Equipo.id_liga == liga_id).all()

    resultados = []
    for equipo in equipos:
        # Obtener todos los partidos finalizados donde participó este equipo
        partidos = db.query(Partido).filter(
            Partido.id_liga == liga_id,
            Partido.estado == "Finalizado",
            (Partido.id_equipo_local == equipo.id_equipo) | (Partido.id_equipo_visitante == equipo.id_equipo)
        ).all()

        victorias = 0
        empates = 0
        derrotas = 0

        for partido in partidos:
            # Determinar si el equipo es local o visitante
            es_local = partido.id_equipo_local == equipo.id_equipo
            goles_equipo = partido.goles_local if es_local else partido.goles_visitante
            goles_rival = partido.goles_visitante if es_local else partido.goles_local

            # Solo contar partidos con resultado válido
            if goles_equipo is not None and goles_rival is not None:
                if goles_equipo > goles_rival:
                    victorias += 1
                elif goles_equipo == goles_rival:
                    empates += 1
                else:
                    derrotas += 1

        partidos_jugados = victorias + empates + derrotas
        porcentaje_victorias = (victorias / partidos_jugados * 100) if partidos_jugados > 0 else 0.0

        resultados.append(EquipoRendimientoResponse(
            id_equipo=equipo.id_equipo,
            nombre=equipo.nombre,
            escudo=equipo.escudo,
            colores=equipo.colores,
            id_liga=equipo.id_liga,
            partidos_jugados=partidos_jugados,
            victorias=victorias,
            empates=empates,
            derrotas=derrotas,
            porcentaje_victorias=round(porcentaje_victorias, 1)
        ))

    # Ordenar por porcentaje de victorias descendente
    resultados.sort(key=lambda x: x.porcentaje_victorias, reverse=True)

    return resultados
