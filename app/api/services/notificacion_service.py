"""
Servicios de lógica de negocio para Notificación.
Maneja la gestión de notificaciones para usuarios, permitiendo consultar,
crear, marcar como leídas y eliminar notificaciones.
"""
from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion
from app.schemas.notificacion import NotificacionCreate
from app.models.usuario_rol import UsuarioRol


def obtener_notificaciones_usuario(db: Session, usuario_id: int):
    """
    Obtiene todas las notificaciones de un usuario específico.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario

    Returns:
        list[Notificacion]: Lista de notificaciones del usuario
    """
    return db.query(Notificacion).filter(
        Notificacion.id_usuario == usuario_id
    ).order_by(Notificacion.created_at.desc()).all()


def obtener_no_leidas(db: Session, usuario_id: int):
    """
    Obtiene solo las notificaciones no leídas de un usuario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario

    Returns:
        list[Notificacion]: Lista de notificaciones no leídas
    """
    return db.query(Notificacion).filter(
        Notificacion.id_usuario == usuario_id,
        Notificacion.leida == False
    ).order_by(Notificacion.created_at.desc()).all()


def crear_notificacion(db: Session, datos: NotificacionCreate):
    """
    Crea una nueva notificación para un usuario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (NotificacionCreate): Datos de la notificación a crear

    Returns:
        Notificacion: Notificación creada
    """
    notificacion = Notificacion(
        id_usuario=datos.id_usuario,
        tipo=datos.tipo,
        titulo=datos.titulo,
        mensaje=datos.mensaje,
        leida=datos.leida,
        id_referencia=datos.id_referencia,
        tipo_referencia=datos.tipo_referencia
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def crear_notificaciones_masivas(db: Session, notificaciones_data: list[dict]):
    """
    Crea múltiples notificaciones en una sola transacción (bulk insert).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        notificaciones_data (list[dict]): Lista de diccionarios con datos de notificaciones

    Returns:
        int: Número de notificaciones creadas
    """
    if not notificaciones_data:
        return 0

    notificaciones = []
    for datos in notificaciones_data:
        notificacion = Notificacion(**datos)
        db.add(notificacion)
        notificaciones.append(notificacion)

    db.commit()

    # Refresh para obtener los IDs generados
    for notif in notificaciones:
        db.refresh(notif)

    return len(notificaciones)


def notificar_seguidores_liga(db: Session, id_liga: int, tipo: str, titulo: str,
                               mensaje: str, tipo_referencia: str = "liga",
                               id_referencia: int = None):
    """
    Envía notificación a todos los seguidores de una liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_liga (int): ID de la liga
        tipo (str): Tipo de notificación
        titulo (str): Título de la notificación
        mensaje (str): Contenido del mensaje
        tipo_referencia (str): Tipo de referencia ("liga", "partido", etc.)
        id_referencia (int | None): ID de la referencia

    Returns:
        int: Número de notificaciones creadas
    """
    from app.models.usuario_sigue_liga import UsuarioSigueLiga

    # Obtener todos los seguidores de la liga
    seguidores = db.query(UsuarioSigueLiga).filter(
        UsuarioSigueLiga.id_liga == id_liga
    ).all()

    if not seguidores:
        return 0

    # Preparar datos para bulk insert
    notificaciones_data = []
    for seguidor in seguidores:
        notificaciones_data.append({
            "id_usuario": seguidor.id_usuario,
            "tipo": tipo,
            "titulo": titulo,
            "mensaje": mensaje,
            "leida": False,
            "id_referencia": id_referencia if id_referencia else id_liga,
            "tipo_referencia": tipo_referencia
        })

    return crear_notificaciones_masivas(db, notificaciones_data)


def notificar_equipo(db: Session, id_equipo: int, tipo: str, titulo: str, mensaje: str,
                     id_referencia: int = None, tipo_referencia: str = "equipo",
                     excluir_ids: set = None):
    """
    Notifica a todos los miembros de un equipo (jugadores + entrenador + delegado).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_equipo (int): ID del equipo
        tipo (str): Tipo de notificación
        titulo (str): Título
        mensaje (str): Mensaje
        id_referencia (int | None): ID de referencia opcional
        tipo_referencia (str): Tipo de referencia
        excluir_ids (set | None): Set de IDs de usuario a excluir

    Returns:
        int: Número de notificaciones creadas
    """
    from app.models.jugador import Jugador
    from app.models.equipo import Equipo

    # Obtener el equipo
    equipo = db.query(Equipo).filter(Equipo.id_equipo == id_equipo).first()
    if not equipo:
        return 0

    # Recopilar todos los IDs de usuario del equipo
    ids_usuario = set()

    # Añadir entrenador
    if equipo.id_entrenador:
        ids_usuario.add(equipo.id_entrenador)

    # Añadir delegado
    if equipo.id_delegado:
        ids_usuario.add(equipo.id_delegado)

    # Añadir todos los jugadores
    jugadores = db.query(Jugador).filter(Jugador.id_equipo == id_equipo).all()
    for jugador in jugadores:
        if jugador.id_usuario:
            ids_usuario.add(jugador.id_usuario)

    # Excluir IDs especificados
    if excluir_ids:
        ids_usuario -= excluir_ids

    if not ids_usuario:
        return 0

    # Preparar datos para bulk insert
    notificaciones_data = []
    for id_usuario in ids_usuario:
        notificaciones_data.append({
            "id_usuario": id_usuario,
            "tipo": tipo,
            "titulo": titulo,
            "mensaje": mensaje,
            "leida": False,
            "id_referencia": id_referencia,
            "tipo_referencia": tipo_referencia
        })

    return crear_notificaciones_masivas(db, notificaciones_data)


def notificar_usuarios_liga(db: Session, id_liga: int, tipo: str, titulo: str,
                            mensaje: str, id_referencia: int = None,
                            tipo_referencia: str = "liga", excluir_ids: set = None):
    """
    Notifica a todos los usuarios con rol en una liga (usuario_rol).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_liga (int): ID de la liga
        tipo (str): Tipo de notificación
        titulo (str): Título de la notificación
        mensaje (str): Contenido del mensaje
        id_referencia (int | None): ID de la referencia opcional
        tipo_referencia (str): Tipo de referencia ("liga", "partido", etc.)
        excluir_ids (set | None): Set de IDs de usuario a excluir

    Returns:
        int: Número de notificaciones creadas
    """
    # Obtener todos los usuarios con rol en la liga
    usuarios_rol = db.query(UsuarioRol).filter(
        UsuarioRol.id_liga == id_liga
    ).all()

    if not usuarios_rol:
        return 0

    # Preparar datos para bulk insert
    notificaciones_data = []
    for usuario_rol in usuarios_rol:
        # Excluir usuarios específicos si se proporcionan
        if excluir_ids and usuario_rol.id_usuario in excluir_ids:
            continue

        notificaciones_data.append({
            "id_usuario": usuario_rol.id_usuario,
            "tipo": tipo,
            "titulo": titulo,
            "mensaje": mensaje,
            "leida": False,
            "id_referencia": id_referencia if id_referencia else id_liga,
            "tipo_referencia": tipo_referencia
        })

    return crear_notificaciones_masivas(db, notificaciones_data)


def marcar_notificacion_leida(db: Session, notificacion_id: int, usuario_id: int):
    """
    Marca una notificación como leída.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        notificacion_id (int): ID de la notificación a marcar
        usuario_id (int): ID del usuario propietario (validación de pertenencia)

    Returns:
        bool: True si se marcó correctamente

    Raises:
        ValueError: Si la notificación no existe o no pertenece al usuario
    """
    # Buscar la notificación y verificar que pertenece al usuario
    notificacion = db.query(Notificacion).filter(
        Notificacion.id_notificacion == notificacion_id,
        Notificacion.id_usuario == usuario_id
    ).first()

    if not notificacion:
        raise ValueError("Notificación no encontrada")

    # Marcar como leída
    notificacion.leida = True
    db.commit()
    return True


def marcar_todas_como_leidas(db: Session, usuario_id: int):
    """
    Marca todas las notificaciones de un usuario como leídas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario

    Returns:
        int: Número de notificaciones marcadas como leídas
    """
    resultado = db.query(Notificacion).filter(
        Notificacion.id_usuario == usuario_id,
        Notificacion.leida == False
    ).update({"leida": True}, synchronize_session=False)

    db.commit()
    return resultado


def eliminar_notificacion(db: Session, notificacion_id: int, usuario_id: int):
    """
    Elimina una notificación.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        notificacion_id (int): ID de la notificación a eliminar
        usuario_id (int): ID del usuario propietario (validación de pertenencia)

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si la notificación no existe o no pertenece al usuario
    """
    # Buscar la notificación y verificar que pertenece al usuario
    notificacion = db.query(Notificacion).filter(
        Notificacion.id_notificacion == notificacion_id,
        Notificacion.id_usuario == usuario_id
    ).first()

    if not notificacion:
        raise ValueError("Notificación no encontrada")

    # Eliminar notificación
    db.delete(notificacion)
    db.commit()
    return True
