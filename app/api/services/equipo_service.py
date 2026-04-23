"""
Servicios de lógica de negocio para Equipo.
Maneja operaciones CRUD de equipos de fútbol, incluyendo gestión de datos,
asociaciones con liga, entrenador y delegado.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from app.models.equipo import Equipo
from app.models.partido import Partido
from app.models.jugador import Jugador
from app.models.usuario import Usuario
from app.models.evento_partido import EventoPartido
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
            Partido.estado == "finalizado",
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


def obtener_detalle_equipo(db: Session, equipo_id: int, liga_id: int = None):
    """
    Obtiene el detalle completo de un equipo incluyendo estadísticas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo
        liga_id (int, optional): ID de la liga para calcular posición y puntos

    Returns:
        dict: Detalle del equipo con estadísticas completas
    """
    equipo = db.query(Equipo).filter(Equipo.id_equipo == equipo_id).first()
    if not equipo:
        return None

    # Calcular estadísticas del equipo
    partidos = db.query(Partido).filter(
        Partido.estado == "finalizado",
        (Partido.id_equipo_local == equipo_id) | (Partido.id_equipo_visitante == equipo_id)
    ).all()

    victorias = 0
    empates = 0
    derrotas = 0
    goles_favor = 0
    goles_contra = 0
    puntos = 0

    for partido in partidos:
        es_local = partido.id_equipo_local == equipo_id
        goles_equipo = partido.goles_local if es_local else partido.goles_visitante
        goles_rival = partido.goles_visitante if es_local else partido.goles_local

        if goles_equipo is not None and goles_rival is not None:
            goles_favor += goles_equipo
            goles_contra += goles_rival

            if goles_equipo > goles_rival:
                victorias += 1
                puntos += 3
            elif goles_equipo == goles_rival:
                empates += 1
                puntos += 1
            else:
                derrotas += 1

    partidos_jugados = victorias + empates + derrotas
    tasa_victoria = round((victorias / partidos_jugados * 100) if partidos_jugados > 0 else 0, 1)

    # Calcular posición en la liga (si se proporciona liga_id)
    posicion_liga = 1
    if liga_id:
        # Obtener todos los equipos de la liga y sus puntos
        equipos_liga = db.query(Equipo).filter(Equipo.id_liga == liga_id).all()
        puntos_equipos = []
        for eq in equipos_liga:
            pts = 0
            parts = db.query(Partido).filter(
                Partido.estado == "finalizado",
                Partido.id_liga == liga_id,
                (Partido.id_equipo_local == eq.id_equipo) | (Partido.id_equipo_visitante == eq.id_equipo)
            ).all()
            for p in parts:
                es_loc = p.id_equipo_local == eq.id_equipo
                g_eq = p.goles_local if es_loc else p.goles_visitante
                g_rival = p.goles_visitante if es_loc else p.goles_local
                if g_eq is not None and g_rival is not None:
                    if g_eq > g_rival:
                        pts += 3
                    elif g_eq == g_rival:
                        pts += 1
            puntos_equipos.append((eq.id_equipo, pts))

        # Ordenar por puntos descendente
        puntos_equipos.sort(key=lambda x: x[1], reverse=True)
        for i, (eq_id, pts) in enumerate(puntos_equipos, 1):
            if eq_id == equipo_id:
                posicion_liga = i
                break

    return {
        "id_equipo": equipo.id_equipo,
        "nombre": equipo.nombre,
        "escudo": equipo.escudo,
        "colores": equipo.colores,
        "id_liga": equipo.id_liga,
        "id_entrenador": equipo.id_entrenador,
        "id_delegado": equipo.id_delegado,
        "ciudad": equipo.ciudad,
        "estadio": equipo.estadio,
        "created_at": equipo.created_at.isoformat() if equipo.created_at else None,
        "updated_at": equipo.updated_at.isoformat() if equipo.updated_at else None,
        "posicion_liga": posicion_liga,
        "puntos": puntos,
        "tasa_victoria": tasa_victoria,
        "goles_favor": goles_favor,
        "goles_contra": goles_contra,
    }


def obtener_proximos_partidos(db: Session, equipo_id: int, limit: int = 5):
    """
    Obtiene los próximos partidos de un equipo (estado: Programado o En Juego).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo
        limit (int): Número máximo de partidos a devolver

    Returns:
        list: Lista de próximos partidos
    """
    partidos = db.query(Partido).filter(
        Partido.estado.in_(["programado", "en_juego"]),
        (Partido.id_equipo_local == equipo_id) | (Partido.id_equipo_visitante == equipo_id)
    ).order_by(Partido.fecha.asc()).limit(limit).all()

    resultados = []
    for partido in partidos:
        equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
        equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

        resultados.append({
            "id_partido": partido.id_partido,
            "fecha": partido.fecha.isoformat() if partido.fecha else None,
            "estado": partido.estado,
            "id_equipo_local": partido.id_equipo_local,
            "id_equipo_visitante": partido.id_equipo_visitante,
            "nombre_equipo_local": equipo_local.nombre if equipo_local else "Unknown",
            "nombre_equipo_visitante": equipo_visitante.nombre if equipo_visitante else "Unknown",
            "escudo_equipo_local": equipo_local.escudo if equipo_local else None,
            "escudo_equipo_visitante": equipo_visitante.escudo if equipo_visitante else None,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
        })

    return resultados


def obtener_ultimos_partidos(db: Session, equipo_id: int, limit: int = 5):
    """
    Obtiene los últimos partidos finalizados de un equipo.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo
        limit (int): Número máximo de partidos a devolver

    Returns:
        list: Lista de últimos partidos con resultado (W/D/L)
    """
    partidos = db.query(Partido).filter(
        Partido.estado == "finalizado",
        (Partido.id_equipo_local == equipo_id) | (Partido.id_equipo_visitante == equipo_id)
    ).order_by(Partido.fecha.desc()).limit(limit).all()

    resultados = []
    for partido in reversed(partidos):  # Ordenar cronológicamente (más antiguo primero)
        es_local = partido.id_equipo_local == equipo_id
        goles_equipo = partido.goles_local if es_local else partido.goles_visitante
        goles_rival = partido.goles_visitante if es_local else partido.goles_local

        resultado = None
        if goles_equipo is not None and goles_rival is not None:
            if goles_equipo > goles_rival:
                resultado = "W"
            elif goles_equipo == goles_rival:
                resultado = "D"
            else:
                resultado = "L"

        equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
        equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

        resultados.append({
            "id_partido": partido.id_partido,
            "fecha": partido.fecha.isoformat() if partido.fecha else None,
            "estado": partido.estado,
            "id_equipo_local": partido.id_equipo_local,
            "id_equipo_visitante": partido.id_equipo_visitante,
            "nombre_equipo_local": equipo_local.nombre if equipo_local else "Unknown",
            "nombre_equipo_visitante": equipo_visitante.nombre if equipo_visitante else "Unknown",
            "escudo_equipo_local": equipo_local.escudo if equipo_local else None,
            "escudo_equipo_visitante": equipo_visitante.escudo if equipo_visitante else None,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
            "resultado": resultado,
        })

    return resultados


def obtener_goleadores_equipo(db: Session, equipo_id: int, limit: int = 3):
    """
    Obtiene los máximos goleadores de un equipo.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo
        limit (int): Número máximo de goleadores a devolver

    Returns:
        list: Lista de jugadores ordenados por goles
    """
    # Subquery para contar goles por jugador
    goles_subquery = db.query(
        EventoPartido.id_jugador,
        func.count(EventoPartido.id_evento).label("goles")
    ).filter(
        EventoPartido.id_jugador.isnot(None),
        EventoPartido.tipo_evento.in_(["Gol", "Gol Propia"])
    ).group_by(EventoPartido.id_jugador).subquery()

    # Obtener jugadores del equipo con sus goles
    jugadores = db.query(
        Jugador,
        Usuario,
        goles_subquery.c.goles
    ).join(
        Usuario, Jugador.id_usuario == Usuario.id_usuario
    ).outerjoin(
        goles_subquery, Jugador.id_jugador == goles_subquery.c.id_jugador
    ).filter(
        Jugador.id_equipo == equipo_id,
        Jugador.activo == True
    ).order_by(
        goles_subquery.c.goles.desc().nullslast()
    ).limit(limit).all()

    resultados = []
    for jugador, usuario, goles in jugadores:
        resultados.append({
            "id_jugador": jugador.id_jugador,
            "id_usuario": jugador.id_usuario,
            "id_equipo": jugador.id_equipo,
            "posicion": jugador.posicion,
            "dorsal": jugador.dorsal,
            "activo": jugador.activo,
            "nombre": usuario.nombre,
            "goles": goles or 0,
            "asistencias": 0,
            "tarjetas_amarillas": 0,
            "tarjetas_rojas": 0,
            "partidos_jugados": 0,
        })

    return resultados


def obtener_plantilla_equipo(db: Session, equipo_id: int):
    """
    Obtiene la plantilla completa de un equipo ordenada por posición.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo

    Returns:
        list: Lista de jugadores con sus estadísticas
    """
    # Subquery para estadísticas de jugadores
    stats_subquery = db.query(
        EventoPartido.id_jugador,
        func.count(case((EventoPartido.tipo_evento == "Gol", 1))).label("goles"),
        func.count(case((EventoPartido.tipo_evento == "Asistencia", 1))).label("asistencias"),
        func.count(case((EventoPartido.tipo_evento.in_(["Tarjeta Amarilla"]), 1))).label("amarillas"),
        func.count(case((EventoPartido.tipo_evento.in_(["Tarjeta Roja", "Segunda Amarilla"]), 1))).label("rojas"),
    ).filter(
        EventoPartido.id_jugador.isnot(None)
    ).group_by(EventoPartido.id_jugador).subquery()

    # Subquery para partidos jugados
    partidos_jugados_subquery = db.query(
        EventoPartido.id_jugador,
        func.count(EventoPartido.id_partido.distinct()).label("partidos")
    ).filter(
        EventoPartido.id_jugador.isnot(None)
    ).group_by(EventoPartido.id_jugador).subquery()

    jugadores = db.query(
        Jugador,
        Usuario,
        stats_subquery,
        partidos_jugados_subquery.c.partidos
    ).join(
        Usuario, Jugador.id_usuario == Usuario.id_usuario
    ).outerjoin(
        stats_subquery, Jugador.id_jugador == stats_subquery.c.id_jugador
    ).outerjoin(
        partidos_jugados_subquery, Jugador.id_jugador == partidos_jugados_subquery.c.id_jugador
    ).filter(
        Jugador.id_equipo == equipo_id,
        Jugador.activo == True
    ).order_by(
        Jugador.posicion,
        Jugador.dorsal
    ).all()

    resultados = []
    for jugador, usuario, stats, partidos_jugados in jugadores:
        resultados.append({
            "id_jugador": jugador.id_jugador,
            "id_usuario": jugador.id_usuario,
            "id_equipo": jugador.id_equipo,
            "posicion": jugador.posicion,
            "dorsal": jugador.dorsal,
            "activo": jugador.activo,
            "nombre": usuario.nombre,
            "goles": stats.goles if stats else 0,
            "asistencias": stats.asistencias if stats else 0,
            "tarjetas_amarillas": stats.amarillas if stats else 0,
            "tarjetas_rojas": stats.rojas if stats else 0,
            "partidos_jugados": partidos_jugados or 0,
            "rating": 0,  # Se puede calcular basado en rendimiento
        })

    return resultados


def obtener_staff_equipo(db: Session, equipo_id: int):
    """
    Obtiene el staff de un equipo (entrenador y capitán).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        equipo_id (int): ID del equipo

    Returns:
        dict: Información del entrenador y capitán
    """
    equipo = db.query(Equipo).filter(Equipo.id_equipo == equipo_id).first()
    if not equipo:
        return None

    # Obtener entrenador
    entrenador = None
    if equipo.id_entrenador:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == equipo.id_entrenador).first()
        if usuario:
            entrenador = {
                "id_usuario": usuario.id_usuario,
                "nombre": usuario.nombre,
            }

    # Obtener capitán (jugador con más partidos o designado)
    capitan = None
    jugador_capitan = db.query(Jugador).filter(
        Jugador.id_equipo == equipo_id,
        Jugador.activo == True
    ).order_by(Jugador.created_at.asc()).first()  # El más antiguo como capitán

    if jugador_capitan:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == jugador_capitan.id_usuario).first()
        if usuario:
            capitan = {
                "id_jugador": jugador_capitan.id_jugador,
                "nombre": usuario.nombre,
                "dorsal": jugador_capitan.dorsal,
            }

    return {
        "entrenador": entrenador,
        "capitan": capitan,
    }
