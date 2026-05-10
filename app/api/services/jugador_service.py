"""
Servicios de lógica de negocio para Jugador.
Maneja operaciones CRUD de jugadores, incluyendo asociación con equipos,
gestión de posiciones, dorsales y estado activo/inactivo.
"""
from sqlalchemy.orm import Session, joinedload
from app.models.jugador import Jugador
from app.models.usuario import Usuario
from app.models.equipo import Equipo
from app.schemas.jugador import JugadorCreate, JugadorUpdate


def _validar_dorsal(dorsal) -> int:
    """Convierte dorsal a int y evita insertar NULL en jugadores.dorsal."""
    if dorsal is None:
        raise ValueError("El dorsal es obligatorio")
    try:
        dorsal_int = int(str(dorsal).strip())
    except ValueError:
        raise ValueError("El dorsal debe ser un número entero")
    if dorsal_int < 0:
        raise ValueError("El dorsal no puede ser negativo")
    return dorsal_int


def crear_jugador(db: Session, datos: JugadorCreate):
    """
    Registra un nuevo jugador en la base de datos.

    Este servicio no exige que el usuario ya pertenezca al equipo, porque esa era
    una validación circular: para pertenecer como jugador primero hay que poder
    crear la fila `jugadores`. La pertenencia queda definida precisamente por
    `Jugador(id_usuario, id_equipo)`.
    """
    usuario = db.query(Usuario).filter(Usuario.id_usuario == datos.id_usuario).first()
    if not usuario:
        raise ValueError(f"El usuario con ID {datos.id_usuario} no existe")

    equipo = db.query(Equipo).filter(Equipo.id_equipo == datos.id_equipo).first()
    if not equipo:
        raise ValueError(f"El equipo con ID {datos.id_equipo} no existe")

    dorsal_int = _validar_dorsal(datos.dorsal)
    posicion_limpia = (datos.posicion or "").strip()
    if not posicion_limpia:
        raise ValueError("La posición es obligatoria")

    jugador_existente = db.query(Jugador).filter(
        Jugador.id_usuario == datos.id_usuario
    ).first()
    if jugador_existente:
        raise ValueError("Este usuario ya está registrado como jugador")

    dorsal_ocupado = db.query(Jugador).filter(
        Jugador.id_equipo == datos.id_equipo,
        Jugador.dorsal == dorsal_int,
        Jugador.activo == True
    ).first()
    if dorsal_ocupado:
        raise ValueError(f"El dorsal {dorsal_int} ya está asignado en este equipo")

    jugador = Jugador(
        id_usuario=datos.id_usuario,
        id_equipo=datos.id_equipo,
        posicion=posicion_limpia,
        dorsal=dorsal_int,
        activo=datos.activo
    )
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    return jugador


def obtener_jugadores(db: Session, equipo_id: int = None, liga_id: int = None, solo_activos: bool = True):
    """Obtiene jugadores, opcionalmente filtrados por equipo o liga."""
    from app.models.equipo import Equipo

    query = db.query(Jugador).options(joinedload(Jugador.usuario))

    if equipo_id is not None:
        query = query.filter(Jugador.id_equipo == equipo_id)
    if liga_id is not None:
        query = query.join(Equipo).filter(Equipo.id_liga == liga_id)
    if solo_activos:
        query = query.filter(Jugador.activo == True)

    jugadores = query.all()

    # Añade el nombre calculado desde Usuario para facilitar respuestas existentes.
    for jugador in jugadores:
        if jugador.usuario:
            jugador.nombre = jugador.usuario.nombre

    return jugadores


def obtener_jugador_por_id(db: Session, jugador_id: int):
    """Busca un jugador por su ID."""
    return db.query(Jugador).filter(Jugador.id_jugador == jugador_id).first()


def actualizar_jugador(db: Session, jugador_id: int, datos: JugadorUpdate):
    """Actualiza los datos de un jugador existente."""
    jugador = obtener_jugador_por_id(db, jugador_id)
    if not jugador:
        raise ValueError("Jugador no encontrado")

    cambios = datos.dict(exclude_unset=True)

    if "dorsal" in cambios:
        cambios["dorsal"] = _validar_dorsal(cambios["dorsal"])

        dorsal_ocupado = db.query(Jugador).filter(
            Jugador.id_equipo == jugador.id_equipo,
            Jugador.dorsal == cambios["dorsal"],
            Jugador.id_jugador != jugador_id,
            Jugador.activo == True
        ).first()
        if dorsal_ocupado:
            raise ValueError(f"El dorsal {cambios['dorsal']} ya está asignado en este equipo")

    if "posicion" in cambios and cambios["posicion"] is not None:
        cambios["posicion"] = cambios["posicion"].strip()
        if not cambios["posicion"]:
            raise ValueError("La posición es obligatoria")

    for campo, valor in cambios.items():
        setattr(jugador, campo, valor)

    db.commit()
    db.refresh(jugador)
    return jugador


def eliminar_jugador(db: Session, jugador_id: int):
    """Elimina un jugador de la base de datos."""
    jugador = obtener_jugador_por_id(db, jugador_id)
    if not jugador:
        raise ValueError("Jugador no encontrado")

    db.delete(jugador)
    db.commit()
