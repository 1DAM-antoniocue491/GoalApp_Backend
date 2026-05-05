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

    REGLA DE NEGOCIO:
    Solo el delegado del equipo LOCAL puede añadir eventos del partido.
    Puede registrar eventos de AMBOS equipos (local y visitante).

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
        ValueError: Si el usuario no es delegado del equipo local o validaciones de sustitución fallan
    """
    # Obtener el partido con ambos equipos
    partido = db.query(Partido).filter(Partido.id_partido == datos.id_partido).options(
        joinedload(Partido.equipo_local),
        joinedload(Partido.equipo_visitante)
    ).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el usuario es delegado del equipo local
    equipo_local = partido.equipo_local

    # Verificar que el usuario tiene el rol de delegate
    rol_delegate = db.query(Rol).filter(Rol.nombre == "delegate").first()
    if not rol_delegate:
        raise ValueError("Rol 'delegate' no encontrado")

    usuario_rol = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_rol == rol_delegate.id_rol
    ).first()

    if not usuario_rol:
        raise ValueError("Solo los delegados pueden crear eventos de partido")

    # Verificar que el usuario es el delegado del equipo LOCAL
    if equipo_local.id_delegado != usuario_id:
        raise ValueError("Solo el delegado del equipo local puede añadir eventos del partido")

    # VALIDACIONES ESPECÍFICAS POR TIPO DE EVENTO
    if datos.tipo_evento == "cambio":
        _validar_sustitucion(db, partido, datos)

    # Crear el evento
    evento = EventoPartido(
        id_partido=datos.id_partido,
        id_jugador=datos.id_jugador,
        id_jugador_sale=datos.id_jugador_sale,  # Nuevo campo para sustituciones
        tipo_evento=datos.tipo_evento,
        minuto=datos.minuto
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)

    # === TRIGGER DE NOTIFICACIÓN DE GOL ===
    if datos.tipo_evento == "GOL":
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

                # Notificar a seguidores de la liga
                from app.api.services.notificacion_service import notificar_seguidores_liga
                notificar_seguidores_liga(
                    db=db,
                    id_liga=partido.id_liga,
                    tipo="gol",
                    titulo=titulo,
                    mensaje=mensaje,
                    id_referencia=partido.id_partido,
                    tipo_referencia="partido"
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
                titulo = f"Sustitución en {equipo.nombre}"
                mensaje = f"Sale {jugador_sale.usuario.nombre}, entra {jugador_entra.usuario.nombre} (min {datos.minuto})"

                # Notificar a todos los miembros del equipo
                from app.api.services.notificacion_service import notificar_equipo
                notificar_equipo(
                    db=db,
                    id_equipo=equipo.id_equipo,
                    tipo="sustitucion",
                    titulo=titulo,
                    mensaje=mensaje,
                    id_referencia=partido.id_partido,
                    tipo_referencia="partido",
                    excluir_ids={usuario_id}  # Excluir al delegado que hizo la acción
                )

    # Si es sustitución, actualizar estados después de crear el evento
    if datos.tipo_evento == "cambio" and datos.id_jugador_sale:
        _actualizar_estados_sustitucion(db, partido, datos, evento.minuto)

    return evento


def obtener_eventos_por_partido(db: Session, partido_id: int):
    """
    Obtiene todos los eventos de un partido específico.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido

    Returns:
        list[EventoPartido]: Lista de eventos ordenados cronológicamente
    """
    return db.query(EventoPartido).filter(EventoPartido.id_partido == partido_id).order_by(EventoPartido.minuto).all()


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
