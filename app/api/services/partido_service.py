"""
Servicios de lógica de negocio para Partido.
Maneja operaciones CRUD de partidos, incluyendo gestión de equipos local y visitante,
marcadores, fechas y estados del partido.
"""
from sqlalchemy.orm import Session, selectinload, aliased
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from itertools import combinations
import json
from app.models.partido import Partido
from app.models.equipo import Equipo
from app.models.jornada import Jornada
from app.models.liga_configuracion import LigaConfiguracion
from app.models.convocatoria_partido import ConvocatoriaPartido
from app.models.alineacion_partido import AlineacionPartido
from app.models.jugador import Jugador
from app.models.evento_partido import EventoPartido
from app.models.estado_jugador_partido import EstadoJugadorPartido
from app.schemas.partido import PartidoCreate, PartidoUpdate, CalendarCreateRequest, FinalizarPartidoRequest


def crear_partido(db: Session, datos: PartidoCreate):
    """
    Crea un nuevo partido en la base de datos.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (PartidoCreate): Datos del partido (liga, equipos, fecha, estado, goles)
    
    Returns:
        Partido: Objeto Partido creado con su ID asignado
    """
    partido = Partido(
        id_liga=datos.id_liga,
        id_equipo_local=datos.id_equipo_local,
        id_equipo_visitante=datos.id_equipo_visitante,
        fecha=datos.fecha,
        estado=datos.estado,
        goles_local=datos.goles_local,
        goles_visitante=datos.goles_visitante
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    return partido


def obtener_partidos(db: Session, liga_id: int = None):
    """
    Obtiene todos los partidos registrados, opcionalmente filtrados por liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int, optional): ID de la liga para filtrar

    Returns:
        list[Partido]: Lista con todos los partidos (filtrados por liga si se proporciona)
    """
    # Usar aliases explícitos para evitar duplicate alias error
    EquipoLocal = aliased(Equipo)
    EquipoVisitante = aliased(Equipo)

    query = db.query(
        Partido,
        EquipoLocal,
        EquipoVisitante
    ).outerjoin(
        EquipoLocal, Partido.id_equipo_local == EquipoLocal.id_equipo
    ).outerjoin(
        EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo
    ).options(
        selectinload(Partido.liga),
        selectinload(Partido.jornada)
    )
    if liga_id is not None:
        query = query.filter(Partido.id_liga == liga_id)

    # Devolver solo los objetos Partido (los equipos se acceden via relación)
    return [partido for partido, _, _ in query.all()]


def obtener_partido_por_id(db: Session, partido_id: int):
    """
    Busca un partido por su ID.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a buscar
    
    Returns:
        Partido: Objeto Partido si existe, None si no se encuentra
    """
    return db.query(Partido).filter(Partido.id_partido == partido_id).first()


def actualizar_partido(db: Session, partido_id: int, datos: PartidoUpdate):
    """
    Actualiza los datos de un partido existente.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a actualizar
        datos (PartidoUpdate): Datos a actualizar (solo campos proporcionados)
    
    Returns:
        Partido: Objeto Partido actualizado
    
    Raises:
        ValueError: Si el partido no existe
    """
    partido = obtener_partido_por_id(db, partido_id)
    if not partido:
        raise ValueError("Partido no encontrado")

    # Actualizar solo los campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(partido, campo, valor)

    db.commit()
    db.refresh(partido)
    return partido


def eliminar_partido(db: Session, partido_id: int):
    """
    Elimina un partido de la base de datos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a eliminar

    Raises:
        ValueError: Si el partido no existe
    """
    partido = obtener_partido_por_id(db, partido_id)
    if not partido:
        raise ValueError("Partido no encontrado")

    db.delete(partido)
    db.commit()


def obtener_partidos_con_equipos(db: Session, liga_id: int = None):
    """
    Obtiene todos los partidos con información de los equipos.
    Usa outer joins para manejar casos donde un equipo haya sido eliminado.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int, optional): ID de la liga para filtrar

    Returns:
        list: Lista de partidos con nombres y escudos de equipos
    """
    # Usar aliases explícitos para evitar duplicate alias error
    EquipoLocal = aliased(Equipo)
    EquipoVisitante = aliased(Equipo)

    # Usar outerjoin para manejar equipos NULL (evita 500 si falta un equipo)
    query = db.query(
        Partido,
        EquipoLocal.nombre.label("nombre_equipo_local"),
        EquipoLocal.escudo.label("escudo_equipo_local"),
        EquipoVisitante.nombre.label("nombre_equipo_visitante"),
        EquipoVisitante.escudo.label("escudo_equipo_visitante")
    ).outerjoin(EquipoLocal, Partido.id_equipo_local == EquipoLocal.id_equipo)\
     .outerjoin(EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo)

    if liga_id is not None:
        query = query.filter(Partido.id_liga == liga_id)

    resultados = []
    for partido, nombre_local, escudo_local, nombre_visitante, escudo_visitante in query.all():
        resultados.append({
            "id_partido": partido.id_partido,
            "id_liga": partido.id_liga,
            "id_jornada": partido.id_jornada,
            "id_equipo_local": partido.id_equipo_local,
            "id_equipo_visitante": partido.id_equipo_visitante,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
            "fecha": partido.fecha.isoformat() if partido.fecha else None,
            "estado": partido.estado,
            "created_at": partido.created_at.isoformat() if partido.created_at else None,
            "updated_at": partido.updated_at.isoformat() if partido.updated_at else None,
            "nombre_equipo_local": nombre_local if nombre_local else "Unknown",
            "escudo_equipo_local": escudo_local,
            "nombre_equipo_visitante": nombre_visitante if nombre_visitante else "Unknown",
            "escudo_equipo_visitante": escudo_visitante,
        })

    return resultados


def obtener_partidos_por_jornada(db: Session, liga_id: int):
    """
    Obtiene los partidos agrupados por jornada.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        list: Lista de jornadas con sus partidos
    """
    # Usar aliases explícitos para evitar duplicate alias error al unir equipos dos veces
    EquipoLocal = aliased(Equipo)
    EquipoVisitante = aliased(Equipo)

    # Consulta con joins explícitos usando aliases para evitar conflicto de tablas
    query = db.query(
        Partido,
        EquipoLocal,
        EquipoVisitante
    ).outerjoin(
        EquipoLocal, Partido.id_equipo_local == EquipoLocal.id_equipo
    ).outerjoin(
        EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo
    ).filter(Partido.id_liga == liga_id)

    resultados_query = query.all()

    # Agrupar por jornada
    jornadas_dict = {}
    for partido, equipo_local, equipo_visitante in resultados_query:
        jornada_num = partido.id_jornada or 1
        if jornada_num not in jornadas_dict:
            jornadas_dict[jornada_num] = []

        jornadas_dict[jornada_num].append({
            "id_partido": partido.id_partido,
            "id_liga": partido.id_liga,
            "id_jornada": partido.id_jornada,
            "id_equipo_local": partido.id_equipo_local,
            "id_equipo_visitante": partido.id_equipo_visitante,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
            "fecha": partido.fecha.isoformat() if partido.fecha else None,
            "estado": partido.estado,
            "created_at": partido.created_at.isoformat() if partido.created_at else None,
            "updated_at": partido.updated_at.isoformat() if partido.updated_at else None,
            "nombre_equipo_local": equipo_local.nombre if equipo_local else "Unknown",
            "escudo_equipo_local": equipo_local.escudo if equipo_local else None,
            "nombre_equipo_visitante": equipo_visitante.nombre if equipo_visitante else "Unknown",
            "escudo_equipo_visitante": equipo_visitante.escudo if equipo_visitante else None,
        })

    # Convertir a lista ordenada
    resultados = []
    for jornada_num in sorted(jornadas_dict.keys()):
        resultados.append({
            "numero": jornada_num,
            "nombre": f"Jornada {jornada_num}",
            "partidos": jornadas_dict[jornada_num],
        })

    return resultados


def obtener_partidos_proximos(db: Session, limit: int = 10):
    """
    Obtiene los próximos partidos programados.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        limit (int): Número máximo de partidos a devolver

    Returns:
        list: Lista de próximos partidos con información de equipos
    """
    # Usar aliases explícitos para evitar duplicate alias error
    EquipoLocal = aliased(Equipo)
    EquipoVisitante = aliased(Equipo)

    # Consulta con joins explícitos usando aliases
    query = db.query(
        Partido,
        EquipoLocal,
        EquipoVisitante
    ).outerjoin(
        EquipoLocal, Partido.id_equipo_local == EquipoLocal.id_equipo
    ).outerjoin(
        EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo
    ).filter(
        Partido.estado == "programado"
    ).order_by(Partido.fecha.asc()).limit(limit)

    resultados = []
    for partido, equipo_local, equipo_visitante in query.all():
        resultados.append({
            "id_partido": partido.id_partido,
            "id_liga": partido.id_liga,
            "id_jornada": partido.id_jornada,
            "id_equipo_local": partido.id_equipo_local,
            "id_equipo_visitante": partido.id_equipo_visitante,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
            "fecha": partido.fecha.isoformat() if partido.fecha else None,
            "estado": partido.estado,
            "nombre_equipo_local": equipo_local.nombre if equipo_local else "Unknown",
            "escudo_equipo_local": equipo_local.escudo if equipo_local else None,
            "nombre_equipo_visitante": equipo_visitante.nombre if equipo_visitante else "Unknown",
            "escudo_equipo_visitante": equipo_visitante.escudo if equipo_visitante else None,
        })

    return resultados


def obtener_partidos_en_vivo(db: Session):
    """
    Obtiene los partidos que están en vivo.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        list: Lista de partidos en vivo con información de equipos
    """
    # Usar aliases explícitos para evitar duplicate alias error
    EquipoLocal = aliased(Equipo)
    EquipoVisitante = aliased(Equipo)

    # Consulta con joins explícitos usando aliases
    query = db.query(
        Partido,
        EquipoLocal,
        EquipoVisitante
    ).outerjoin(
        EquipoLocal, Partido.id_equipo_local == EquipoLocal.id_equipo
    ).outerjoin(
        EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo
    ).filter(Partido.estado == "en_juego")

    resultados = []
    for partido, equipo_local, equipo_visitante in query.all():
        resultados.append({
            "id_partido": partido.id_partido,
            "id_liga": partido.id_liga,
            "id_jornada": partido.id_jornada,
            "id_equipo_local": partido.id_equipo_local,
            "id_equipo_visitante": partido.id_equipo_visitante,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
            "fecha": partido.fecha.isoformat() if partido.fecha else None,
            "estado": partido.estado,
            "nombre_equipo_local": equipo_local.nombre if equipo_local else "Unknown",
            "escudo_equipo_local": equipo_local.escudo if equipo_local else None,
            "nombre_equipo_visitante": equipo_visitante.nombre if equipo_visitante else "Unknown",
            "escudo_equipo_visitante": equipo_visitante.escudo if equipo_visitante else None,
        })

    return resultados


def crear_calendario(db: Session, liga_id: int, config: CalendarCreateRequest):
    """
    Crea automáticamente todos los partidos de una liga basándose en la configuración.
    Usa algoritmo round-robin para distribuir equipos en jornadas.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga para la que crear el calendario
        config (CalendarCreateRequest): Configuración del calendario (tipo, fecha inicio, días, hora)

    Returns:
        dict: Mensaje de confirmación y número de partidos creados

    Raises:
        ValueError: Si no hay suficientes equipos, ya existe calendario o configuración inválida
    """
    # Verificar si ya existe un calendario (partidos programados para esta liga)
    partidos_existentes = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado == "programado"
    ).count()

    if partidos_existentes > 0:
        raise ValueError(f"La liga ya tiene un calendario generado con {partidos_existentes} partidos. Elimina el calendario existente antes de crear uno nuevo.")

    # Obtener equipos de la liga
    equipos = db.query(Equipo).filter(Equipo.id_liga == liga_id).all()

    if len(equipos) < 2:
        raise ValueError("Se necesitan al menos 2 equipos para crear un calendario")

    # Parsear fecha de inicio
    try:
        fecha_inicio = datetime.strptime(config.fecha_inicio, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")

    # Parsear hora
    try:
        hora_parts = config.hora.split(":")
        hora = int(hora_parts[0])
        minuto = int(hora_parts[1]) if len(hora_parts) > 1 else 0
    except (ValueError, IndexError):
        raise ValueError("Formato de hora inválido. Use HH:MM")

    # Algoritmo round-robin
    equipos_lista = list(equipos)

    # Si hay número impar de equipos, añadir un "bye" (equipo fantasma)
    if len(equipos_lista) % 2 != 0:
        equipos_lista.append(None)

    num_equipos = len(equipos_lista)
    num_jornadas = num_equipos - 1
    partidos_por_jornada = num_equipos // 2

    # Encontrar la primera fecha válida (día seleccionado)
    fecha_actual = fecha_inicio
    while True:
        dia_semana = fecha_actual.weekday()  # 0=Lunes, 6=Domingo
        # Convertir a formato backend (1=Lunes, 0=Domingo)
        dia_backend = dia_semana + 1 if dia_semana < 6 else 0
        if dia_backend in config.dias_partido:
            break
        fecha_actual += timedelta(days=1)

    # Crear jornadas primero (ida)
    jornadas_ida = []
    fecha_jornada = fecha_actual
    for i in range(num_jornadas):
        jornada = Jornada(
            id_liga=liga_id,
            numero=i + 1,
            nombre=f"Jornada {i + 1}",
            fecha_inicio=fecha_jornada.replace(hour=hora, minute=minuto),
            fecha_fin=fecha_jornada.replace(hour=hora+2, minute=minuto)  # 2 horas de ventana
        )
        db.add(jornada)
        db.flush()  # Obtener el ID generado
        jornadas_ida.append(jornada.id_jornada)
        fecha_jornada += timedelta(weeks=1)

    # Crear partidos de ida
    partidos_creados = 0
    fecha_actual = fecha_inicio

    # Reiniciar equipos para el cálculo
    equipos_lista = list(equipos)
    if len(equipos_lista) % 2 != 0:
        equipos_lista.append(None)

    for jornada_idx in range(num_jornadas):
        # Encontrar fecha válida para esta jornada
        while True:
            dia_semana = fecha_actual.weekday()
            dia_backend = dia_semana + 1 if dia_semana < 6 else 0
            if dia_backend in config.dias_partido:
                break
            fecha_actual += timedelta(days=1)

        id_jornada = jornadas_ida[jornada_idx]

        # Generar emparejamientos de esta jornada
        for i in range(partidos_por_jornada):
            local_idx = i
            visitante_idx = num_equipos - 1 - i

            local = equipos_lista[local_idx]
            visitante = equipos_lista[visitante_idx]

            # Saltar si alguno es None (equipo fantasma)
            if local is None or visitante is None:
                continue

            # Crear partido con la fecha calculada
            fecha_partido = fecha_actual.replace(hour=hora, minute=minuto)
            partido = Partido(
                id_liga=liga_id,
                id_jornada=id_jornada,
                id_equipo_local=local.id_equipo,
                id_equipo_visitante=visitante.id_equipo,
                fecha=fecha_partido,
                estado="programado",  # Normalizado a minúscula para coincidir con el enum
                goles_local=None,
                goles_visitante=None
            )
            db.add(partido)
            partidos_creados += 1

        # Rotar equipos para la siguiente jornada (algoritmo round-robin)
        equipos_lista = [equipos_lista[0]] + [equipos_lista[-1]] + equipos_lista[1:-1]
        fecha_actual += timedelta(weeks=1)

    # Si es ida y vuelta, crear la vuelta
    if config.tipo == "ida_vuelta":
        # Reiniciar equipos para la vuelta
        equipos_lista = list(equipos)
        if len(equipos_lista) % 2 != 0:
            equipos_lista.append(None)

        # La vuelta comienza una semana después de la última jornada de ida
        fecha_actual += timedelta(weeks=1)

        # Crear jornadas de vuelta
        jornadas_vuelta = []
        fecha_jornada = fecha_actual
        for i in range(num_jornadas):
            jornada = Jornada(
                id_liga=liga_id,
                numero=num_jornadas + i + 1,
                nombre=f"Jornada {num_jornadas + i + 1} (Vuelta)",
                fecha_inicio=fecha_jornada.replace(hour=hora, minute=minuto),
                fecha_fin=fecha_jornada.replace(hour=hora+2, minute=minuto)
            )
            db.add(jornada)
            db.flush()
            jornadas_vuelta.append(jornada.id_jornada)
            fecha_jornada += timedelta(weeks=1)

        # Crear partidos de vuelta
        fecha_actual = fecha_inicio + timedelta(weeks=num_jornadas)
        for jornada_idx in range(num_jornadas):
            # Encontrar fecha válida
            while True:
                dia_semana = fecha_actual.weekday()
                dia_backend = dia_semana + 1 if dia_semana < 6 else 0
                if dia_backend in config.dias_partido:
                    break
                fecha_actual += timedelta(days=1)

            id_jornada = jornadas_vuelta[jornada_idx]

            for i in range(partidos_por_jornada):
                local_idx = i
                visitante_idx = num_equipos - 1 - i

                local = equipos_lista[local_idx]
                visitante = equipos_lista[visitante_idx]

                if local is None or visitante is None:
                    continue

                # Invertir localía para la vuelta
                fecha_partido = fecha_actual.replace(hour=hora, minute=minuto)
                partido = Partido(
                    id_liga=liga_id,
                    id_jornada=id_jornada,
                    id_equipo_local=visitante.id_equipo,  # Invertido
                    id_equipo_visitante=local.id_equipo,   # Invertido
                    fecha=fecha_partido,
                    estado="programado",
                    goles_local=None,
                    goles_visitante=None
                )
                db.add(partido)
                partidos_creados += 1

            # Rotar equipos
            equipos_lista = [equipos_lista[0]] + [equipos_lista[-1]] + equipos_lista[1:-1]
            fecha_actual += timedelta(weeks=1)

    db.commit()

    # Guardar configuración del calendario
    config_liga = db.query(LigaConfiguracion).filter(LigaConfiguracion.id_liga == liga_id).first()
    if config_liga:
        config_liga.calendario_tipo = config.tipo
        config_liga.calendario_fecha_inicio = config.fecha_inicio
        config_liga.calendario_dias_partido = json.dumps(config.dias_partido)
        config_liga.calendario_hora = config.hora
        db.commit()

    total_jornadas = len(jornadas_ida) if config.tipo == "ida" else len(jornadas_ida) + len(jornadas_vuelta)

    return {
        "mensaje": f"Calendario creado con {partidos_creados} partidos distribuidos en {total_jornadas} jornadas",
        "partidos_creados": partidos_creados
    }


def obtener_config_calendario(db: Session, liga_id: int):
    """
    Obtiene la configuración guardada del calendario automático para una liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        dict: Configuración del calendario o None si no existe

    Raises:
        ValueError: Si la liga no tiene configuración de calendario
    """
    config_liga = db.query(LigaConfiguracion).filter(LigaConfiguracion.id_liga == liga_id).first()

    if not config_liga or not config_liga.calendario_tipo:
        raise ValueError("La liga no tiene configuración de calendario automático")

    return {
        "tipo": config_liga.calendario_tipo,
        "fecha_inicio": config_liga.calendario_fecha_inicio,
        "dias_partido": json.loads(config_liga.calendario_dias_partido) if config_liga.calendario_dias_partido else [],
        "hora": config_liga.calendario_hora
    }


def eliminar_calendario(db: Session, liga_id: int):
    """
    Elimina todos los partidos y jornadas de una liga.
    Solo elimina partidos en estado 'programado'.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        dict: Mensaje de confirmación y número de partidos/jornadas eliminados

    Raises:
        ValueError: Si hay partidos en juego o finalizados
    """
    # Verificar si hay partidos en_juego o finalizados
    partidos_bloqueados = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado.in_(["en_juego", "finalizado"])
    ).count()

    if partidos_bloqueados > 0:
        raise ValueError(f"No se puede eliminar el calendario con {partidos_bloqueados} partidos en juego o finalizados")

    # Contar partidos a eliminar
    partidos_count = db.query(Partido).filter(Partido.id_liga == liga_id).count()

    # Obtener jornadas de la liga
    jornadas = db.query(Jornada).filter(Jornada.id_liga == liga_id).all()
    jornadas_count = len(jornadas)

    # Eliminar partidos (cascade delete eliminaría automáticamente, pero lo hacemos explícito)
    db.query(Partido).filter(Partido.id_liga == liga_id).delete(synchronize_session=False)

    # Eliminar jornadas
    for jornada in jornadas:
        db.delete(jornada)

    # Limpiar configuración de calendario
    config_liga = db.query(LigaConfiguracion).filter(LigaConfiguracion.id_liga == liga_id).first()
    if config_liga:
        config_liga.calendario_tipo = None
        config_liga.calendario_fecha_inicio = None
        config_liga.calendario_dias_partido = None
        config_liga.calendario_hora = None

    db.commit()

    return {
        "mensaje": "Calendario eliminado correctamente",
        "partidos_eliminados": partidos_count,
        "jornadas_eliminadas": jornadas_count
    }


def actualizar_calendario(db: Session, liga_id: int, config: CalendarCreateRequest):
    """
    Actualiza el calendario automático: elimina partidos programados y crea nuevo calendario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        config (CalendarCreateRequest): Nueva configuración del calendario

    Returns:
        dict: Mensaje de confirmación y número de partidos creados/eliminados

    Raises:
        ValueError: Si hay partidos en juego o finalizados
    """
    # Verificar si hay partidos en_juego o finalizados
    partidos_bloqueados = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado.in_(["en_juego", "finalizado"])
    ).count()

    if partidos_bloqueados > 0:
        raise ValueError(f"No se puede actualizar el calendario con {partidos_bloqueados} partidos en juego o finalizados")

    # Contar partidos programados a eliminar
    partidos_programados = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado == "programado"
    ).count()

    # Eliminar partidos programados
    db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado == "programado"
    ).delete(synchronize_session=False)

    # Eliminar jornadas existentes
    db.query(Jornada).filter(Jornada.id_liga == liga_id).delete(synchronize_session=False)

    db.commit()

    # Crear nuevo calendario con la configuración actualizada
    resultado = crear_calendario(db, liga_id, config)

    return {
        "mensaje": "Calendario actualizado correctamente",
        "partidos_creados": resultado["partidos_creados"],
        "partidos_eliminados": partidos_programados
    }


def iniciar_partido(db: Session, partido_id: int, usuario_id: int):
    """
    Inicia un partido cambiando su estado a 'en_juego'.

    Validaciones:
    - Usuario es admin o delegado asignado al partido
    - Partido está en estado 'programado'
    - Fecha del partido >= hoy
    - Ambos equipos tienen exactamente 11 titulares
    - Ambos equipos tienen al menos 1 portero entre los titulares

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a iniciar
        usuario_id (int): ID del usuario que inicia el partido

    Returns:
        Partido: Objeto Partido actualizado

    Raises:
        ValueError: Si el partido no existe, no está en estado programado,
                   o los equipos no tienen la alineación requerida
    """
    # Obtener partido con relaciones
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Validar estado
    if partido.estado != "programado":
        raise ValueError(f"El partido debe estar en estado 'programado', estado actual: {partido.estado}")

    # Validar fecha (debe ser hoy o posterior)
    hoy = datetime.now().date()
    fecha_partido = partido.fecha.date()
    if fecha_partido < hoy:
        raise ValueError("No se puede iniciar un partido con fecha pasada")

    # Validar alineación de ambos equipos
    for id_equipo in [partido.id_equipo_local, partido.id_equipo_visitante]:
        # Obtener titulares (11 jugadores) - hacer join con Jugador para filtrar por equipo
        from sqlalchemy.orm import joinedload
        titulares = db.query(AlineacionPartido).join(
            Jugador, AlineacionPartido.id_jugador == Jugador.id_jugador
        ).filter(
            AlineacionPartido.id_partido == partido_id,
            Jugador.id_equipo == id_equipo,
            AlineacionPartido.titular == True
        ).all()

        if len(titulares) != 11:
            raise ValueError(f"El equipo {id_equipo} debe tener exactamente 11 titulares, tiene {len(titulares)}")

        # Validar al menos 1 portero entre los titulares
        ids_jugadores = [a.id_jugador for a in titulares]
        jugadores = db.query(Jugador).filter(
            Jugador.id_jugador.in_(ids_jugadores),
            Jugador.posicion.ilike("%portero%")
        ).all()

        if len(jugadores) < 1:
            raise ValueError(f"El equipo {id_equipo} debe tener al menos 1 portero entre los titulares")

    # Cambiar estado a 'en_juego'
    partido.estado = "en_juego"

    # Inicializar estados de los jugadores
    _inicializar_estados_jugadores(db, partido, [partido.id_equipo_local, partido.id_equipo_visitante])

    db.commit()
    db.refresh(partido)

    return partido


def _inicializar_estados_jugadores(db: Session, partido: Partido, ids_equipos: list[int]):
    """
    Inicializa los estados de los jugadores al inicio del partido:
    - Once inicial (titulares) = 'jugando'
    - Resto de convocados = 'suplente'
    - Jugadores no convocados = no se registran (no pueden participar)

    Args:
        db (Session): Sesión de base de datos
        partido (Partido): Objeto del partido
        ids_equipos (list[int]): IDs de los equipos a inicializar
    """
    for id_equipo in ids_equipos:
        # Obtener jugadores convocados para este partido (join con Jugador para filtrar por equipo)
        convocados = db.query(ConvocatoriaPartido).join(
            Jugador, ConvocatoriaPartido.id_jugador == Jugador.id_jugador
        ).filter(
            ConvocatoriaPartido.id_partido == partido.id_partido,
            Jugador.id_equipo == id_equipo
        ).all()

        if not convocados:
            # Si no hay convocados registrados, usar todos los jugadores del equipo
            jugadores_equipo = db.query(Jugador).filter(
                Jugador.id_equipo == id_equipo,
                Jugador.activo == True
            ).all()
            ids_convocados = [j.id_jugador for j in jugadores_equipo]
        else:
            ids_convocados = [c.id_jugador for c in convocados]

        # Obtener titulares de la alineación (join con Jugador para filtrar por equipo)
        titulares = db.query(AlineacionPartido).join(
            Jugador, AlineacionPartido.id_jugador == Jugador.id_jugador
        ).filter(
            AlineacionPartido.id_partido == partido.id_partido,
            Jugador.id_equipo == id_equipo,
            AlineacionPartido.titular == True
        ).all()
        ids_titulares = [a.id_jugador for a in titulares]

        # Crear registros de estado para cada jugador convocado
        for id_jugador in ids_convocados:
            estado = "jugando" if id_jugador in ids_titulares else "suplente"
            minuto_entrada = 0 if id_jugador in ids_titulares else None

            estado_registro = EstadoJugadorPartido(
                id_partido=partido.id_partido,
                id_jugador=id_jugador,
                id_equipo=id_equipo,
                estado=estado,
                minuto_entrada=minuto_entrada,
                minuto_salida=None
            )
            db.add(estado_registro)


def finalizar_partido(db: Session, partido_id: int, datos: FinalizarPartidoRequest, usuario_id: int):
    """
    Finaliza un partido registrando el resultado y el MVP.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a finalizar
        datos (FinalizarPartidoRequest): Datos del resultado y MVP
        usuario_id (int): ID del usuario que finaliza el partido

    Returns:
        Partido: Objeto Partido actualizado

    Raises:
        ValueError: Si el partido no existe o no está en estado 'en_juego'
    """
    # Obtener partido
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Validar estado
    if partido.estado != "en_juego":
        raise ValueError(f"El partido debe estar 'en_juego' para finalizarlo, estado actual: {partido.estado}")

    # Actualizar resultado
    partido.goles_local = datos.goles_local
    partido.goles_visitante = datos.goles_visitante
    partido.estado = "finalizado"

    # Crear evento MVP
    mvp_evento = EventoPartido(
        id_partido=partido_id,
        id_jugador=datos.id_mvp,
        tipo_evento="mvp",
        minuto=90,  # MVP se registra al final del partido
        puntuacion_mvp=datos.puntuacion_mvp,
        incidencias=datos.incidencias
    )
    db.add(mvp_evento)
    db.commit()
    db.refresh(partido)

    return partido
