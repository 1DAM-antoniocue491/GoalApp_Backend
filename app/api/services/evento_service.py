"""
Servicios de lógica de negocio para EventoPartido.
Maneja la gestión de eventos de partido (goles, tarjetas, sustituciones, etc.)
y su registro en la base de datos.
"""
from sqlalchemy.orm import Session
from app.models.evento_partido import EventoPartido
from app.models.partido import Partido
from app.models.usuario_rol import UsuarioRol
from app.models.rol import Rol
from app.schemas.eventos import EventoPartidoCreate


def crear_evento(db: Session, datos: EventoPartidoCreate, usuario_id: int):
    """
    Registra un nuevo evento en un partido.

    REGLA DE NEGOCIO:
    Solo el delegado del equipo LOCAL puede añadir eventos del partido.
    Al delegado del equipo visitante NO se le permite añadir eventos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (EventoPartidoCreate): Datos del evento (partido, jugador, tipo, minuto)
        usuario_id (int): ID del usuario que crea el evento

    Returns:
        EventoPartido: Objeto EventoPartido creado con su ID asignado

    Raises:
        ValueError: Si el usuario no es delegado del equipo local
    """
    # Obtener el partido
    partido = db.query(Partido).filter(Partido.id_partido == datos.id_partido).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar que el usuario es delegado del equipo local
    # El delegado está asociado al equipo a través del campo id_delegado
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

    # Crear el evento
    evento = EventoPartido(
        id_partido=datos.id_partido,
        id_jugador=datos.id_jugador,
        tipo_evento=datos.tipo_evento,
        minuto=datos.minuto
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
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
