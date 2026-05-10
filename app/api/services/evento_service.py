"""
Servicios de lógica de negocio para EventoPartido.
Maneja la gestión de eventos de partido (goles, tarjetas, sustituciones, etc.)
y su registro en la base de datos.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.evento_partido import EventoPartido
from app.models.partido import Partido
from app.models.usuario_rol import UsuarioRol
from app.models.rol import Rol
from app.models.estado_jugador_partido import EstadoJugadorPartido
from app.models.equipo import Equipo
from app.models.jugador import Jugador
from app.schemas.eventos import EventoPartidoCreate


def crear_evento(db: Session, datos: EventoPartidoCreate, usuario_id: int):
    """
    Registra un nuevo evento en un partido.

    REGLAS DE NEGOCIO:
    - El ADMIN de la liga puede registrar eventos de AMBOS equipos (local y visitante)
    - El DELEGADO del equipo local SOLO puede registrar eventos del equipo LOCAL
    - El DELEGADO del equipo visitante SOLO puede registrar eventos del equipo VISITANTE
    - Se valida que el jugador del evento pertenece al equipo cuyo delegado está registrando

    Para sustituciones:
    - Valida que el jugador que entra está en suplentes
    - Valida que el jugador que sale está jugando
    - Actualiza los estados en estado_jugador_partido

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (EventoPartidoCreate): Datos del evento (partido, jugador, tipo, minuto, id_jugador_sale)
        usuario_id (int): ID del usuario que crea el evento

    Returns:
        EventoPartido: Objeto EventoPartido creado con su ID asignado

    Raises:
        ValueError: Si el usuario no tiene permiso (no es admin ni delegado) o si el delegado
                    intenta registrar eventos de un equipo que no es el suyo
    """
    # Obtener el partido con ambos equipos
    partido = db.query(Partido).filter(Partido.id_partido == datos.id_partido).options(
        joinedload(Partido.equipo_local),
        joinedload(Partido.equipo_visitante)
    ).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # ============================================================
    # VALIDACIÓN DE PERMISOS: Admin O Delegado (local o visitante)
    # ============================================================
    es_admin = False
    equipo_delegado_id = None  # ID del equipo cuyo delegado está registrando

    # 1. Verificar si es ADMIN de la liga (puede registrar eventos de AMBOS equipos)
    rol_admin = db.query(Rol).filter(Rol.nombre == "admin").first()
    if rol_admin:
        admin_liga = db.query(UsuarioRol).filter(
            UsuarioRol.id_usuario == usuario_id,
            UsuarioRol.id_rol == rol_admin.id_rol,
            UsuarioRol.id_liga == partido.id_liga
        ).first()
        if admin_liga:
            es_admin = True

    # 2. Si no es admin, verificar si es DELEGADO (local o visitante)
    if not es_admin:
        # Verificar si es delegado del equipo local
        if partido.equipo_local and partido.equipo_local.id_delegado == usuario_id:
            equipo_delegado_id = partido.equipo_local.id_equipo
        # Verificar si es delegado del equipo visitante
        elif partido.equipo_visitante and partido.equipo_visitante.id_delegado == usuario_id:
            equipo_delegado_id = partido.equipo_visitante.id_equipo

    if not es_admin and not equipo_delegado_id:
        raise ValueError("Solo el administrador de la liga o los delegados de los equipos pueden añadir eventos del partido")

    # 3. VALIDACIÓN ADICIONAL: El delegado solo puede registrar eventos de jugadores de SU equipo
    # El admin puede registrar eventos de cualquier equipo
    if not es_admin and equipo_delegado_id:
        # Obtener el equipo del jugador que está registrando el evento
        jugador = db.query(Jugador).filter(Jugador.id_jugador == datos.id_jugador).first()
        if not jugador:
            raise ValueError("Jugador no encontrado")
        if jugador.id_equipo != equipo_delegado_id:
            raise ValueError("El delegado solo puede registrar eventos de jugadores de su propio equipo")
    # ============================================================

    # VALIDACIONES ESPECÍFICAS POR TIPO DE EVENTO
    if datos.tipo_evento == "cambio":
        _validar_sustitucion(db, partido, datos)

    # Crear el evento
    evento = EventoPartido(
        id_partido=datos.id_partido,
        id_jugador=datos.id_jugador,
        id_jugador_sale=datos.id_jugador_sale,
        tipo_evento=datos.tipo_evento,
        minuto=datos.minuto,
        incidencias=datos.incidencias
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)

    # === TRIGGER DE NOTIFICACIÓN DE GOL ===
    if datos.tipo_evento == "gol":
        # Obtener info del jugador y equipo
        jugador = db.query(Jugador).filter(
            Jugador.id_jugador == datos.id_jugador
        ).first()

        if jugador:
            equipo = db.query(Equipo).filter(
                Equipo.id_equipo == jugador.id_equipo
            ).first()

            if equipo:
                titulo = f"¡GOL DE {equipo.nombre.upper()}!"
                mensaje = f"{jugador.usuario.nombre} marca gol en el minuto {datos.minuto}"

                # Notificar solo a usuarios con rol en la liga (admins, delegados, entrenadores)
                from app.api.services.notificacion_service import notificar_usuarios_liga
                notificar_usuarios_liga(
                    db=db,
                    id_liga=partido.id_liga,
                    tipo="gol",
                    titulo=titulo,
                    mensaje=mensaje,
                    id_referencia=partido.id_partido,
                    tipo_referencia="partido",
                    excluir_ids={usuario_id}  # Excluir quien registró el gol
                )

    # === TRIGGER DE NOTIFICACIÓN DE SUSTITUCIÓN ===
    if datos.tipo_evento == "cambio":
        # Obtener info del jugador que sale y el que entra
        jugador_entra = db.query(Jugador).filter(
            Jugador.id_jugador == datos.id_jugador
        ).options(joinedload(Jugador.usuario)).first()
        jugador_sale = db.query(Jugador).filter(
            Jugador.id_jugador == datos.id_jugador_sale
        ).options(joinedload(Jugador.usuario)).first() if datos.id_jugador_sale else None

        if jugador_entra and jugador_sale:
            # Ambos jugadores son del mismo equipo (ya validado en _validar_sustitucion)
            equipo = db.query(Equipo).filter(
                Equipo.id_equipo == jugador_entra.id_equipo
            ).first()

            if equipo:
                # Notificaciones personalizadas solo a jugadores involucrados + delegado
                from app.api.services.notificacion_service import crear_notificaciones_masivas

                notificaciones_data = []

                # Notificar al jugador que entra
                if jugador_entra.id_usuario and jugador_entra.id_usuario != usuario_id:
                    notificaciones_data.append({
                        "id_usuario": jugador_entra.id_usuario,
                        "tipo": "sustitucion",
                        "titulo": "Has entrado al campo",
                        "mensaje": f"Entras al campo en el minuto {datos.minuto}",
                        "leida": False,
                        "id_referencia": partido.id_partido,
                        "tipo_referencia": "partido"
                    })

                # Notificar al jugador que sale
                if jugador_sale.id_usuario and jugador_sale.id_usuario != usuario_id:
                    notificaciones_data.append({
                        "id_usuario": jugador_sale.id_usuario,
                        "tipo": "sustitucion",
                        "titulo": "Has sido sustituido",
                        "mensaje": f"Sales del campo en el minuto {datos.minuto}",
                        "leida": False,
                        "id_referencia": partido.id_partido,
                        "tipo_referencia": "partido"
                    })

                # Notificar al delegado del equipo (si existe y no es quien registró)
                if equipo.id_delegado and equipo.id_delegado != usuario_id:
                    mensaje_delegado = f"Sale {jugador_sale.usuario.nombre}, entra {jugador_entra.usuario.nombre} (min {datos.minuto})"
                    notificaciones_data.append({
                        "id_usuario": equipo.id_delegado,
                        "tipo": "sustitucion",
                        "titulo": "Sustitución en tu equipo",
                        "mensaje": mensaje_delegado,
                        "leida": False,
                        "id_referencia": partido.id_partido,
                        "tipo_referencia": "partido"
                    })

                if notificaciones_data:
                    crear_notificaciones_masivas(db, notificaciones_data)

    # Si es sustitución, actualizar estados después de crear el evento
    if datos.tipo_evento == "cambio" and datos.id_jugador_sale:
        _actualizar_estados_sustitucion(db, partido, datos, evento.minuto)

    return evento


def obtener_eventos_por_partido(db: Session, partido_id: int):
    """
    Obtiene todos los eventos de un partido específico con información del jugador y equipo.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido

    Returns:
        list[EventoPartido]: Lista de eventos ordenados cronológicamente
    """
    eventos = db.query(EventoPartido).options(
        joinedload(EventoPartido.jugador).joinedload(Jugador.equipo)
    ).filter(
        EventoPartido.id_partido == partido_id
    ).order_by(EventoPartido.minuto).all()

    # Poblar campos adicionales para el response
    for evento in eventos:
        if evento.jugador:
            evento.nombre_jugador = f"{evento.jugador.nombre} {evento.jugador.apellido or ''}".strip()
            if evento.jugador.equipo:
                evento.id_equipo = evento.jugador.equipo.id_equipo
                evento.nombre_equipo = evento.jugador.equipo.nombre

    return eventos


def _validar_sustitucion(db: Session, partido: Partido, datos: EventoPartidoCreate):
    """
    Valida una sustitución:
    - El jugador que entra debe estar en la lista de suplentes
    - El jugador que sale debe estar jugando
    - Ambos jugadores deben ser del mismo equipo

    Args:
        db (Session): Sesión de base de datos
        partido (Partido): Objeto del partido
        datos (EventoPartidoCreate): Datos de la sustitución

    Raises:
        ValueError: Si las validaciones fallan
    """
    if not datos.id_jugador_sale:
        raise ValueError("Para una sustitución es requerido el campo id_jugador_sale")

    # Obtener estados actuales de ambos jugadores en este partido
    estado_entra = db.query(EstadoJugadorPartido).filter(
        EstadoJugadorPartido.id_partido == partido.id_partido,
        EstadoJugadorPartido.id_jugador == datos.id_jugador
    ).first()

    estado_sale = db.query(EstadoJugadorPartido).filter(
        EstadoJugadorPartido.id_partido == partido.id_partido,
        EstadoJugadorPartido.id_jugador == datos.id_jugador_sale
    ).first()

    # Validar que ambos jugadores tengan estado registrado
    if not estado_entra:
        raise ValueError(f"El jugador {datos.id_jugador} no tiene estado registrado en este partido")
    if not estado_sale:
        raise ValueError(f"El jugador {datos.id_jugador_sale} no tiene estado registrado en este partido")

    # Validar que el jugador que entra está en suplentes
    if estado_entra.estado != "suplente":
        raise ValueError(f"El jugador {datos.id_jugador} no está en la lista de suplentes (estado actual: {estado_entra.estado})")

    # Validar que el jugador que sale está jugando
    if estado_sale.estado != "jugando":
        raise ValueError(f"El jugador {datos.id_jugador_sale} no está jugando (estado actual: {estado_sale.estado})")

    # Validar que ambos jugadores son del mismo equipo
    if estado_entra.id_equipo != estado_sale.id_equipo:
        raise ValueError("El jugador que entra y el que sale deben ser del mismo equipo")


def _actualizar_estados_sustitucion(db: Session, partido: Partido, datos: EventoPartidoCreate, minuto: int):
    """
    Actualiza los estados de los jugadores después de una sustitución:
    - Jugador que entra: 'suplente' → 'jugando', minuto_entrada = minuto
    - Jugador que sale: 'jugando' → 'suplente', minuto_salida = minuto

    Args:
        db (Session): Sesión de base de datos
        partido (Partido): Objeto del partido
        datos (EventoPartidoCreate): Datos de la sustitución
        minuto (int): Minuto de la sustitución
    """
    # Actualizar jugador que entra
    estado_entra = db.query(EstadoJugadorPartido).filter(
        EstadoJugadorPartido.id_partido == partido.id_partido,
        EstadoJugadorPartido.id_jugador == datos.id_jugador
    ).first()

    if estado_entra:
        estado_entra.estado = "jugando"
        estado_entra.minuto_entrada = minuto
        estado_entra.minuto_salida = None
        estado_entra.updated_at = db.query(func.now()).scalar()

    # Actualizar jugador que sale
    estado_sale = db.query(EstadoJugadorPartido).filter(
        EstadoJugadorPartido.id_partido == partido.id_partido,
        EstadoJugadorPartido.id_jugador == datos.id_jugador_sale
    ).first()

    if estado_sale:
        estado_sale.estado = "suplente"
        estado_sale.minuto_salida = minuto
        estado_sale.updated_at = db.query(func.now()).scalar()

    db.commit()
