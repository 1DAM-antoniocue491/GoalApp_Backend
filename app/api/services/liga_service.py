"""
Servicios de lógica de negocio para Liga.
Maneja operaciones CRUD de ligas/competiciones, incluyendo gestión de
nombres y temporadas, y asignación automática del rol admin al creador.
"""
from sqlalchemy.orm import Session, noload, joinedload, selectinload
from typing import List
from collections import defaultdict

from app.models.liga import Liga
from app.models.liga_configuracion import LigaConfiguracion
from app.models.equipo import Equipo
from app.models.partido import Partido
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.models.usuario import Usuario
from app.models.notificacion import Notificacion
from app.schemas.liga import LigaCreate, LigaUpdate
from app.schemas.clasificacion import ClasificacionItem
from app.schemas.gestion_usuarios import UsuarioRolUpdate, UsuarioEstadoUpdate, UsuarioLigaResponse


def _refresh_liga(db: Session, liga_id: int) -> Liga:
    """Recarga una liga desde la BD cargando configuracion para serialización."""
    return db.query(Liga).options(
        noload(Liga.equipos),
        noload(Liga.usuario_roles),
        joinedload(Liga.configuracion),
    ).filter(Liga.id_liga == liga_id).one()


def crear_liga(db: Session, datos: LigaCreate, id_usuario_creador: int = None):
    """
    Crea una nueva liga en la base de datos y su configuración por defecto.

    Si se proporciona id_usuario_creador, asigna automáticamente el rol admin
    al usuario creador para esta liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (LigaCreate): Datos de la liga (nombre, temporada, categoria, cantidad_partidos, duracion_partido, logo_url)
        id_usuario_creador (int, optional): ID del usuario que crea la liga

    Returns:
        Liga: Objeto Liga creado con su ID asignado

    Raises:
        ValueError: Si el usuario ya tiene una liga con ese nombre
    """
    # Verificar si el usuario ya tiene una liga con ese nombre
    if id_usuario_creador:
        # Buscar si el usuario ya es admin de una liga con ese nombre
        ligas_usuario = db.query(Liga).join(UsuarioRol).join(Rol).filter(
            Liga.nombre == datos.nombre,
            UsuarioRol.id_usuario == id_usuario_creador,
            UsuarioRol.id_liga == Liga.id_liga,
            Rol.nombre == "admin"
        ).first()
        
        if ligas_usuario:
            raise ValueError(f"Ya tienes una liga con el nombre '{datos.nombre}'")
    liga = Liga(
        nombre=datos.nombre,
        temporada=datos.temporada,
        categoria=datos.categoria,
        activa=datos.activa,
        cantidad_partidos=getattr(datos, 'cantidad_partidos', None),
        duracion_partido=getattr(datos, 'duracion_partido', None),
        logo_url=getattr(datos, 'logo_url', None)
    )
    db.add(liga)
    db.flush()  # Obtener el ID de la liga sin hacer commit

    # Crear configuración por defecto
    configuracion = LigaConfiguracion(id_liga=liga.id_liga)
    db.add(configuracion)

    # Si se proporcionó un usuario creador, asignar rol admin para esta liga
    if id_usuario_creador:
        # Buscar el rol admin (asumiendo que existe con nombre "admin")
        rol_admin = db.query(Rol).filter(Rol.nombre == "admin").first()
        if rol_admin:
            # Verificar que no exista ya esta asignación
            asignacion_existente = db.query(UsuarioRol).filter(
                UsuarioRol.id_usuario == id_usuario_creador,
                UsuarioRol.id_rol == rol_admin.id_rol,
                UsuarioRol.id_liga == liga.id_liga
            ).first()

            if not asignacion_existente:
                # Crear la asignación de rol admin para esta liga
                usuario_rol = UsuarioRol(
                    id_usuario=id_usuario_creador,
                    id_rol=rol_admin.id_rol,
                    id_liga=liga.id_liga
                )
                db.add(usuario_rol)

    # Enviar notificación a todos los usuarios del sistema
    usuarios = db.query(Usuario).all()
    notificaciones = []
    for usuario in usuarios:
        notificacion = Notificacion(
            id_usuario=usuario.id_usuario,
            tipo="liga_actualizacion",
            titulo=f"Nueva liga creada: {liga.nombre}",
            mensaje=f"Se ha creado una nueva liga '{liga.nombre}' ({liga.temporada}). ¡Únete para participar!",
            leida=False,
            id_referencia=liga.id_liga,
            tipo_referencia="liga"
        )
        notificaciones.append(notificacion)
        db.add(notificacion)

    db.commit()
    return _refresh_liga(db, liga.id_liga)


def obtener_ligas(db: Session):
    """
    Obtiene todas las ligas registradas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        list[Liga]: Lista con todas las ligas
    """
    return db.query(Liga).options(
        noload(Liga.equipos),
        noload(Liga.configuracion),
        noload(Liga.usuario_roles),
    ).all()


def obtener_liga_por_id(db: Session, liga_id: int):
    """
    Busca una liga por su ID.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a buscar

    Returns:
        Liga: Objeto Liga si existe, None si no se encuentra
    """
    return db.query(Liga).options(
        noload(Liga.equipos),
        noload(Liga.configuracion),
        noload(Liga.usuario_roles),
    ).filter(Liga.id_liga == liga_id).first()


def actualizar_liga(db: Session, liga_id: int, datos: LigaUpdate):
    """
    Actualiza los datos de una liga existente.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a actualizar
        datos (LigaUpdate): Datos a actualizar (nombre, temporada, categoria, activa, cantidad_partidos, duracion_partido, logo_url)

    Returns:
        Liga: Objeto Liga actualizado

    Raises:
        ValueError: Si la liga no existe
    """
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    # Actualizar campos si se proporcionan
    if datos.nombre is not None:
        liga.nombre = datos.nombre
    if datos.temporada is not None:
        liga.temporada = datos.temporada
    if datos.categoria is not None:
        liga.categoria = datos.categoria
    if datos.activa is not None:
        liga.activa = datos.activa
    if datos.cantidad_partidos is not None:
        liga.cantidad_partidos = datos.cantidad_partidos
    if datos.duracion_partido is not None:
        liga.duracion_partido = datos.duracion_partido
    if datos.logo_url is not None:
        liga.logo_url = datos.logo_url

    db.commit()
    return _refresh_liga(db, liga.id_liga)


def verificar_admin_liga(db: Session, liga_id: int, id_usuario: int) -> None:
    """
    Verifica que el usuario sea administrador de la liga indicada.

    Busca en la tabla usuario_rol si existe una asignación con rol "admin"
    para el usuario y la liga proporcionados.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        id_usuario (int): ID del usuario

    Raises:
        PermissionError: Si el usuario no es admin de la liga
    """
    rol_admin = db.query(Rol).filter(Rol.nombre == "admin").first()
    if not rol_admin:
        raise PermissionError("No tienes permisos para realizar esta acción en esta liga")

    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == id_usuario,
        UsuarioRol.id_rol == rol_admin.id_rol,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise PermissionError("No tienes permisos para realizar esta acción en esta liga")


def reactivar_liga(db: Session, liga_id: int, id_usuario: int = None) -> Liga:
    """
    Reactiva una liga que estaba inactiva.

    Solo permite reactivar si la liga está inactiva.
    Si se proporciona id_usuario, verifica que sea admin de la liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a reactivar
        id_usuario (int, optional): ID del usuario que ejecuta la acción

    Returns:
        Liga: Objeto Liga reactivado

    Raises:
        ValueError: Si la liga no existe o ya está activa
        PermissionError: Si el usuario no es admin de la liga
    """
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    if liga.activa:
        raise ValueError("La liga ya está activa")

    # Verificar permisos si se proporcionó el usuario
    if id_usuario is not None:
        verificar_admin_liga(db, liga_id, id_usuario)

    liga.activa = True
    db.commit()
    return _refresh_liga(db, liga.id_liga)


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
    return _refresh_liga(db, liga.id_liga)


def eliminar_liga(db: Session, liga_id: int):
    """
    Elimina una liga de la base de datos junto con todos sus dependientes.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga a eliminar

    Raises:
        ValueError: Si la liga no existe
    """
    # Cargar la liga con todas sus relaciones para que cascade delete funcione
    liga = db.query(Liga).options(
        joinedload(Liga.equipos),
        joinedload(Liga.configuracion),
        joinedload(Liga.usuario_roles),
        joinedload(Liga.jornadas),
        joinedload(Liga.invitaciones),
        joinedload(Liga.seguidores),
        joinedload(Liga.partidos),
    ).filter(Liga.id_liga == liga_id).first()

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


def obtener_usuarios_liga(db: Session, liga_id: int) -> list[UsuarioLigaResponse]:
    """
    Obtiene todos los usuarios de una liga con su rol y estado.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        list[UsuarioLigaResponse]: Lista de usuarios con su información de rol

    Raises:
        ValueError: Si la liga no existe
    """
    from sqlalchemy.orm import joinedload

    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    usuarios_roles = db.query(UsuarioRol).options(
        joinedload(UsuarioRol.usuario),
        joinedload(UsuarioRol.rol)
    ).filter(
        UsuarioRol.id_liga == liga_id
    ).all()

    resultado = []
    for ur in usuarios_roles:
        resultado.append(UsuarioLigaResponse(
            id_usuario_rol=ur.id_usuario_rol,
            id_usuario=ur.id_usuario,
            nombre_usuario=ur.usuario.nombre,
            email=ur.usuario.email,
            id_rol=ur.id_rol,
            nombre_rol=ur.rol.nombre,
            activo=bool(ur.activo)
        ))
    return resultado


def actualizar_rol_usuario(db: Session, liga_id: int, usuario_id: int, datos: UsuarioRolUpdate) -> UsuarioLigaResponse:
    """
    Actualiza el rol de un usuario en una liga específica.

    Validaciones:
    - El usuario debe pertenecer a la liga
    - El rol debe existir
    - Si el nuevo rol es 'entrenador', el usuario debe tener un equipo asignado o asignarlo

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        usuario_id (int): ID del usuario
        datos (UsuarioRolUpdate): Datos con el nuevo rol

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario

    Raises:
        ValueError: Si la liga, usuario o rol no existen
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Verificar que el rol existe
    rol = db.query(Rol).filter(Rol.id_rol == datos.id_rol).first()
    if not rol:
        raise ValueError("Rol no encontrado")

    # Buscar la asignación usuario-rol-liga
    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise ValueError("El usuario no pertenece a esta liga")

    # Si el nuevo rol es 'entrenador', verificar que tenga equipo
    if rol.nombre == 'entrenador':
        equipo = db.query(Equipo).filter(
            Equipo.id_liga == liga_id,
            Equipo.id_entrenador == usuario_id
        ).first()
        if not equipo:
            raise ValueError("El usuario debe tener un equipo asignado para ser entrenador")

    # Actualizar el rol
    asignacion.id_rol = datos.id_rol
    db.commit()

    # Recargar y retornar
    asignacion_actualizada = db.query(UsuarioRol).join(Usuario).join(Rol).filter(
        UsuarioRol.id_usuario_rol == asignacion.id_usuario_rol
    ).first()

    return UsuarioLigaResponse(
        id_usuario_rol=asignacion_actualizada.id_usuario_rol,
        id_usuario=asignacion_actualizada.id_usuario,
        nombre_usuario=asignacion_actualizada.usuario.nombre_usuario,
        email=asignacion_actualizada.usuario.email,
        id_rol=asignacion_actualizada.id_rol,
        nombre_rol=asignacion_actualizada.rol.nombre,
        activo=bool(asignacion_actualizada.activo)
    )


def actualizar_estado_usuario(db: Session, liga_id: int, usuario_id: int, datos: UsuarioEstadoUpdate) -> UsuarioLigaResponse:
    """
    Actualiza el estado (activo/pendiente) de un usuario en una liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        usuario_id (int): ID del usuario
        datos (UsuarioEstadoUpdate): Datos con el nuevo estado

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario

    Raises:
        ValueError: Si la liga o usuario no existen, o el usuario no pertenece a la liga
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Buscar la asignación usuario-rol-liga
    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise ValueError("El usuario no pertenece a esta liga")

    # Actualizar el estado
    asignacion.activo = 1 if datos.activo else 0
    db.commit()

    # Recargar y retornar
    asignacion_actualizada = db.query(UsuarioRol).join(Usuario).join(Rol).filter(
        UsuarioRol.id_usuario_rol == asignacion.id_usuario_rol
    ).first()

    return UsuarioLigaResponse(
        id_usuario_rol=asignacion_actualizada.id_usuario_rol,
        id_usuario=asignacion_actualizada.id_usuario,
        nombre_usuario=asignacion_actualizada.usuario.nombre_usuario,
        email=asignacion_actualizada.usuario.email,
        id_rol=asignacion_actualizada.id_rol,
        nombre_rol=asignacion_actualizada.rol.nombre,
        activo=bool(asignacion_actualizada.activo)
    )


def eliminar_usuario_liga(db: Session, liga_id: int, usuario_id: int) -> dict:
    """
    Elimina un usuario de una liga.

    Validaciones:
    - No se puede eliminar al único administrador de la liga
    - El usuario debe pertenecer a la liga

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        usuario_id (int): ID del usuario

    Returns:
        dict: Mensaje de confirmación

    Raises:
        ValueError: Si la liga o usuario no existen, el usuario no pertenece a la liga,
                   o es el único admin
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise ValueError("Liga no encontrada")

    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Buscar la asignación usuario-rol-liga
    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise ValueError("El usuario no pertenece a esta liga")

    # Verificar que no sea el único admin
    rol_admin = db.query(Rol).filter(Rol.nombre == "admin").first()
    if rol_admin and asignacion.id_rol == rol_admin.id_rol:
        # Contar cuántos admins hay en la liga
        total_admins = db.query(UsuarioRol).filter(
            UsuarioRol.id_liga == liga_id,
            UsuarioRol.id_rol == rol_admin.id_rol
        ).count()

        if total_admins <= 1:
            raise ValueError("No se puede eliminar al único administrador de la liga")

    # Eliminar la asignación
    db.delete(asignacion)
    db.commit()

    return {"mensaje": f"Usuario {usuario.nombre_usuario} eliminado de la liga {liga.nombre}"}
