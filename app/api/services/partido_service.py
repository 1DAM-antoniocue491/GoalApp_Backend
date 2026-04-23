"""
Servicios de lógica de negocio para Partido.
Maneja operaciones CRUD de partidos, incluyendo gestión de equipos local y visitante,
marcadores, fechas y estados del partido.
"""
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from datetime import datetime, timedelta
from itertools import combinations
from app.models.partido import Partido
from app.models.equipo import Equipo
from app.models.jornada import Jornada
from app.schemas.partido import PartidoCreate, PartidoUpdate, CalendarCreateRequest


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
    query = db.query(Partido).options(
        selectinload(Partido.liga),
        selectinload(Partido.jornada),
        selectinload(Partido.equipo_local),
        selectinload(Partido.equipo_visitante)
    )
    if liga_id is not None:
        query = query.filter(Partido.id_liga == liga_id)
    return query.all()


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

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int, optional): ID de la liga para filtrar

    Returns:
        list: Lista de partidos con nombres y escudos de equipos
    """
    EquipoVisitante = Equipo  # Alias para el equipo visitante

    query = db.query(
        Partido,
        Equipo.nombre.label("nombre_equipo_local"),
        Equipo.escudo.label("escudo_equipo_local"),
        EquipoVisitante.nombre.label("nombre_equipo_visitante"),
        EquipoVisitante.escudo.label("escudo_equipo_visitante")
    ).join(Equipo, Partido.id_equipo_local == Equipo.id_equipo)\
     .join(EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo)

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
            "nombre_equipo_local": nombre_local,
            "escudo_equipo_local": escudo_local,
            "nombre_equipo_visitante": nombre_visitante,
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
    partidos = db.query(Partido).filter(Partido.id_liga == liga_id).all()

    # Agrupar por jornada
    jornadas_dict = {}
    for partido in partidos:
        jornada_num = partido.id_jornada or 1
        if jornada_num not in jornadas_dict:
            jornadas_dict[jornada_num] = []

        # Obtener equipos
        equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
        equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

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
    partidos = db.query(Partido).filter(
        Partido.estado == "programado"
    ).order_by(Partido.fecha.asc()).limit(limit).all()

    resultados = []
    for partido in partidos:
        equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
        equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

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
    partidos = db.query(Partido).filter(Partido.estado == "en_juego").all()

    resultados = []
    for partido in partidos:
        equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
        equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

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
            "nombre_equipo_visitante": equipo_visitante.nombre if equipo_local else "Unknown",
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
        ValueError: Si no hay suficientes equipos o configuración inválida
    """
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

    total_jornadas = len(jornadas_ida) if config.tipo == "ida" else len(jornadas_ida) + len(jornadas_vuelta)

    return {
        "mensaje": f"Calendario creado con {partidos_creados} partidos distribuidos en {total_jornadas} jornadas",
        "partidos_creados": partidos_creados
    }
