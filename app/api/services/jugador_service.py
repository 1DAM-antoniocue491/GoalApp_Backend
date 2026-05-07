"""
Servicios de lógica de negocio para Jugador.
Maneja operaciones CRUD de jugadores, incluyendo su asociación con equipos,
gestión de posiciones, dorsales y estado activo/inactivo.
"""
from sqlalchemy.orm import Session
from app.models.jugador import Jugador
from app.models.usuario import Usuario
from app.models.equipo import Equipo
from app.schemas.jugador import JugadorCreate, JugadorUpdate


def crear_jugador(db: Session, datos: JugadorCreate):
    """
    Registra un nuevo jugador en la base de datos.

    Valida que:
    - El usuario padre existe
    - El usuario pertenece al equipo (es miembro del equipo: entrenador, delegado o jugador existente)

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (JugadorCreate): Datos del jugador (usuario, equipo, posición, dorsal, activo)

    Returns:
        Jugador: Objeto Jugador creado con su ID asignado

    Raises:
        ValueError: Si el usuario no existe, el equipo no existe, o el usuario no pertenece al equipo
    """
    # Validar que el usuario padre existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == datos.id_usuario).first()
    if not usuario:
        raise ValueError(f"El usuario con ID {datos.id_usuario} no existe")

    # Validar que el equipo existe
    equipo = db.query(Equipo).filter(Equipo.id_equipo == datos.id_equipo).first()
    if not equipo:
        raise ValueError(f"El equipo con ID {datos.id_equipo} no existe")

    # Validar que el usuario pertenece al equipo (es entrenador, delegado, o ya es jugador)
    es_entrenador = (equipo.id_entrenador == datos.id_usuario)
    es_delegado = (equipo.id_delegado == datos.id_usuario)
    es_jugador_existente = db.query(Jugador).filter(
        Jugador.id_usuario == datos.id_usuario,
        Jugador.id_equipo == datos.id_equipo
    ).first() is not None

    if not (es_entrenador or es_delegado or es_jugador_existente):
        raise ValueError(
            f"El usuario {datos.id_usuario} no pertenece al equipo {datos.id_equipo}. "
            "Solo usuarios que son entrenador, delegado o jugador del equipo pueden ser registrados como jugador."
        )

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


def obtener_jugadores(db: Session, equipo_id: int = None, liga_id: int = None, solo_activos: bool = True):
    """
    Obtiene todos los jugadores registrados, opcionalmente filtrados por equipo o liga.
    Por defecto solo devuelve jugadores activos (activo=True).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int, optional): ID del equipo para filtrar
        liga_id (int, optional): ID de la liga para filtrar (filtra jugadores de equipos de esa liga)
        solo_activos (bool, optional): Si True (default), filtra solo activos. False para todos.

    Returns:
        list[Jugador]: Lista de jugadores (filtrados si se proporciona equipo_id o liga_id)
    """
    from app.models.equipo import Equipo
    query = db.query(Jugador)
    if equipo_id is not None:
        query = query.filter(Jugador.id_equipo == equipo_id)
    if liga_id is not None:
        query = query.join(Equipo).filter(Equipo.id_liga == liga_id)

    # Filtro por defecto: solo activos
    if solo_activos:
        query = query.filter(Jugador.activo == True)

    return query.all()


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
