"""
Servicios de lógica de negocio para Partido.
Maneja operaciones CRUD de partidos, incluyendo gestión de equipos local y visitante,
marcadores, fechas y estados del partido.
"""
from sqlalchemy.orm import Session, selectinload, aliased
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from itertools import combinations
import json
import math
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
from app.api.services.notificacion_service import notificar_usuarios_liga, notificar_equipo


def crear_partido(db: Session, datos: PartidoCreate):
    """
    Crea un nuevo partido en la base de datos.
    Si no se proporciona id_jornada, busca o crea una jornada automática para esa fecha.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (PartidoCreate): Datos del partido (liga, equipos, fecha, estado, goles)

    Returns:
        Partido: Objeto Partido creado con su ID asignado

    Raises:
        ValueError: Si la fecha no es futura, equipos son iguales, ya existe partido duplicado
                   o la liga ya tiene un calendario generado
    """
    # Validar que no haya un calendario generado (partidos en estado 'programado')
    partidos_programados = db.query(Partido).filter(
        Partido.id_liga == datos.id_liga,
        Partido.estado == "programado"
    ).count()

    if partidos_programados > 0:
        raise ValueError("La liga ya tiene un calendario generado. No se pueden crear partidos manuales.")

    # Validar fecha futura
    if datos.fecha < datetime.now(timezone.utc).replace(tzinfo=None):
        raise ValueError("La fecha del partido debe ser futura")

    # Validar que los equipos sean diferentes
    if datos.id_equipo_local == datos.id_equipo_visitante:
        raise ValueError("El equipo local y visitante deben ser diferentes")

    # Validar que no exista un partido duplicado en la misma liga
    duplicado = db.query(Partido).filter(
        Partido.id_liga == datos.id_liga,
        Partido.id_equipo_local == datos.id_equipo_local,
        Partido.id_equipo_visitante == datos.id_equipo_visitante,
        Partido.fecha == datos.fecha
    ).first()

    if duplicado:
        raise ValueError("Ya existe un partido programado entre estos equipos en esta fecha")

    # Validar que no haya enfrentamiento inverso en la misma fecha
    duplicado_inverso = db.query(Partido).filter(
        Partido.id_liga == datos.id_liga,
        Partido.id_equipo_local == datos.id_equipo_visitante,
        Partido.id_equipo_visitante == datos.id_equipo_local,
        Partido.fecha == datos.fecha
    ).first()

    if duplicado_inverso:
        raise ValueError("Ya existe un enfrentamiento entre estos equipos en esta fecha")

    # Determinar id_jornada: usar proporcionado o auto-asignar
    id_jornada = datos.id_jornada

    if id_jornada is None:
        # Buscar o crear jornada para la fecha del partido
        fecha_partido = datos.fecha
        jornada_existente = db.query(Jornada).filter(
            Jornada.id_liga == datos.id_liga,
            Jornada.fecha_inicio <= fecha_partido,
            Jornada.fecha_fin >= fecha_partido
        ).first()

        if jornada_existente:
            id_jornada = jornada_existente.id_jornada
        else:
            # Crear nueva jornada "manual" para esta fecha
            fecha_str = fecha_partido.strftime('%Y-%m-%d')
            jornada_manual = Jornada(
                id_liga=datos.id_liga,
                numero=-1,  # Número especial para jornadas manuales
                nombre=f"Jornada Manual {fecha_str}",
                fecha_inicio=fecha_partido,
                fecha_fin=fecha_partido + timedelta(hours=2)
            )
            db.add(jornada_manual)
            db.flush()  # Obtener ID generado
            id_jornada = jornada_manual.id_jornada

    partido = Partido(
        id_liga=datos.id_liga,
        id_equipo_local=datos.id_equipo_local,
        id_equipo_visitante=datos.id_equipo_visitante,
        fecha=datos.fecha,
        id_jornada=id_jornada,  # Siempre asignado (proporcionado o auto-generado)
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


def actualizar_partido(db: Session, partido_id: int, datos: PartidoUpdate, usuario_id: int):
    """
    Actualiza los datos de un partido existente.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a actualizar
        datos (PartidoUpdate): Datos a actualizar (solo campos proporcionados)
        usuario_id (int): ID del usuario que realiza la actualización
    
    Returns:
        Partido: Objeto Partido actualizado
    
    Raises:
        ValueError: Si el partido no existe o el usuario no tiene permisos
    """
    partido = obtener_partido_por_id(db, partido_id)
    if not partido:
        raise ValueError("Partido no encontrado")

    # Verificar permisos: admin de la liga, o entrenador/delegado de algun equipo
    from app.models.usuario_rol import UsuarioRol, Rol
    
    equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
    equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()
    
    usuario_roles = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id
    ).all()
    roles_usuario = set()
    ligas_usuario = {}
    for ur in usuario_roles:
        rol_nombre = db.query(Rol).filter(Rol.id_rol == ur.id_rol).first()
        if rol_nombre:
            roles_usuario.add(rol_nombre.nombre)
            ligas_usuario[rol_nombre.nombre] = ur.id_liga
    
    es_admin_global = "admin" in roles_usuario
    es_admin_liga = es_admin_global and ligas_usuario.get("admin") == partido.id_liga
    es_entrenador_local = "coach" in roles_usuario and equipo_local and ligas_usuario.get("coach") == partido.id_liga
    es_entrenador_visitante = "coach" in roles_usuario and equipo_visitante and ligas_usuario.get("coach") == partido.id_liga
    es_delegado_local = "delegate" in roles_usuario and equipo_local and ligas_usuario.get("delegate") == partido.id_liga
    es_delegado_visitante = "delegate" in roles_usuario and equipo_visitante and ligas_usuario.get("delegate") == partido.id_liga
    
    if not (es_admin_liga or es_entrenador_local or es_entrenador_visitante or
            es_delegado_local or es_delegado_visitante):
        raise ValueError("No tienes permisos para editar este partido")

    # Actualizar solo los campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        # Si es datetime naive, asignarle zona horaria UTC
        if isinstance(valor, datetime) and valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
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
    # Incluir Jornada para obtener el campo 'numero' real
    query = db.query(
        Partido,
        EquipoLocal,
        EquipoVisitante,
        Jornada
    ).outerjoin(
        EquipoLocal, Partido.id_equipo_local == EquipoLocal.id_equipo
    ).outerjoin(
        EquipoVisitante, Partido.id_equipo_visitante == EquipoVisitante.id_equipo
    ).outerjoin(
        Jornada, Partido.id_jornada == Jornada.id_jornada
    ).filter(Partido.id_liga == liga_id)

    resultados_query = query.all()

    # Agrupar por jornada usando el campo 'numero' real de la jornada
    jornadas_dict = {}
    for partido, equipo_local, equipo_visitante, jornada in resultados_query:
        # Usar el campo 'numero' de la jornada (1, 2, 3...) en lugar del id_jornada autoincremental
        jornada_num = jornada.numero if jornada else (partido.id_jornada or 1)
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


def obtener_partidos_proximos(db: Session, limit: int = 10, liga_id: int = None):
    """
    Obtiene los próximos partidos programados.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        limit (int): Número máximo de partidos a devolver
        liga_id (int, optional): ID de la liga para filtrar

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
    )

    # Filtrar por liga si se proporciona
    if liga_id is not None:
        query = query.filter(Partido.id_liga == liga_id)

    query = query.order_by(Partido.fecha.asc()).limit(limit)

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


def obtener_partidos_en_vivo(db: Session, liga_id: int = None):
    """
    Obtiene los partidos que están en vivo.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int, optional): ID de la liga para filtrar

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

    # Filtrar por liga si se proporciona
    if liga_id is not None:
        query = query.filter(Partido.id_liga == liga_id)

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
            fecha_inicio=fecha_jornada.replace(hour=hora, minute=minuto, tzinfo=timezone.utc),
            fecha_fin=fecha_jornada.replace(hour=hora+2, minute=minuto, tzinfo=timezone.utc)  # 2 horas de ventana
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

    # Calcular distribución de partidos por día
    dias_seleccionados = len(config.dias_partido)
    partidos_por_dia = math.ceil(partidos_por_jornada / dias_seleccionados) if dias_seleccionados > 0 else partidos_por_jornada

    for jornada_idx in range(num_jornadas):
        # Encontrar primer día válido para esta jornada
        while True:
            dia_semana = fecha_actual.weekday()
            dia_backend = dia_semana + 1 if dia_semana < 6 else 0
            if dia_backend in config.dias_partido:
                break
            fecha_actual += timedelta(days=1)

        id_jornada = jornadas_ida[jornada_idx]

        # Crear partidos distribuidos en los días seleccionados
        dia_index = 0
        partidos_en_dia_actual = 0
        fecha_jornada_actual = fecha_actual

        for i in range(partidos_por_jornada):
            # Avanzar al siguiente día si se completó el cupo del día actual
            if partidos_en_dia_actual >= partidos_por_dia and dias_seleccionados > 1:
                dia_index = (dia_index + 1) % dias_seleccionados
                partidos_en_dia_actual = 0

                # Avanzar fecha al siguiente día válido
                fecha_jornada_actual += timedelta(days=1)
                while True:
                    dia_semana = fecha_jornada_actual.weekday()
                    dia_backend = dia_semana + 1 if dia_semana < 6 else 0
                    if dia_backend in config.dias_partido:
                        break
                    fecha_jornada_actual += timedelta(days=1)

            # Crear partido con la fecha calculada
            fecha_partido = fecha_jornada_actual.replace(hour=hora, minute=minuto, tzinfo=timezone.utc)
            local_idx = i
            visitante_idx = num_equipos - 1 - i

            local = equipos_lista[local_idx]
            visitante = equipos_lista[visitante_idx]

            # Saltar si alguno es None (equipo fantasma)
            if local is None or visitante is None:
                continue

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
            partidos_en_dia_actual += 1

        # Rotar equipos para la siguiente jornada (algoritmo round-robin)
        equipos_lista = [equipos_lista[0]] + [equipos_lista[-1]] + equipos_lista[1:-1]
        # Avanzar fecha_actual para la próxima jornada (semana siguiente desde el último día usado)
        fecha_actual = fecha_jornada_actual + timedelta(days=1)

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

        # Calcular distribución de partidos por día para vuelta
        partidos_por_dia_vuelta = math.ceil(partidos_por_jornada / dias_seleccionados) if dias_seleccionados > 0 else partidos_por_jornada

        for jornada_idx in range(num_jornadas):
            # Encontrar primer día válido para esta jornada
            while True:
                dia_semana = fecha_actual.weekday()
                dia_backend = dia_semana + 1 if dia_semana < 6 else 0
                if dia_backend in config.dias_partido:
                    break
                fecha_actual += timedelta(days=1)

            id_jornada = jornadas_vuelta[jornada_idx]

            # Crear partidos distribuidos en los días seleccionados
            dia_index = 0
            partidos_en_dia_actual = 0
            fecha_jornada_actual = fecha_actual

            for i in range(partidos_por_jornada):
                # Avanzar al siguiente día si se completó el cupo del día actual
                if partidos_en_dia_actual >= partidos_por_dia_vuelta and dias_seleccionados > 1:
                    dia_index = (dia_index + 1) % dias_seleccionados
                    partidos_en_dia_actual = 0

                    # Avanzar fecha al siguiente día válido
                    fecha_jornada_actual += timedelta(days=1)
                    while True:
                        dia_semana = fecha_jornada_actual.weekday()
                        dia_backend = dia_semana + 1 if dia_semana < 6 else 0
                        if dia_backend in config.dias_partido:
                            break
                        fecha_jornada_actual += timedelta(days=1)

                # Invertir localía para la vuelta
                fecha_partido = fecha_jornada_actual.replace(hour=hora, minute=minuto, tzinfo=timezone.utc)
                local_idx = i
                visitante_idx = num_equipos - 1 - i

                local = equipos_lista[local_idx]
                visitante = equipos_lista[visitante_idx]

                if local is None or visitante is None:
                    continue

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
                partidos_en_dia_actual += 1

            # Rotar equipos
            equipos_lista = [equipos_lista[0]] + [equipos_lista[-1]] + equipos_lista[1:-1]
            # Avanzar fecha_actual para la próxima jornada
            fecha_actual = fecha_jornada_actual + timedelta(days=1)

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

    Validaciones (en orden):
    1. Partido existe
    2. Partido está en estado 'programado'
    3. Usuario es entrenador o delegado de alguno de los equipos
    4. Fecha/hora del partido ha llegado
    5. Ambos equipos tienen exactamente 11 titulares en la convocatoria
    6. Ambos equipos tienen al menos 1 portero entre los titulares

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        partido_id (int): ID del partido a iniciar
        usuario_id (int): ID del usuario que inicia el partido

    Returns:
        Partido: Objeto Partido actualizado

    Raises:
        ValueError: Si el partido no existe, no está en estado programado,
                   el usuario no tiene permisos, la fecha no ha llegado,
                   o los equipos no tienen la convocatoria requerida
    """
    # Obtener partido con relaciones
    partido = db.query(Partido).filter(Partido.id_partido == partido_id).first()
    if not partido:
        raise ValueError("Partido no encontrado")

    # Validar estado
    if partido.estado != "programado":
        raise ValueError(f"El partido debe estar en estado 'programado', estado actual: {partido.estado}")

    # Validar permisos: admin de la liga, o entrenador/delegado de alguno de los equipos puede iniciar
    # Cargar equipos para obtener entrenador y delegado
    equipo_local = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_local).first()
    equipo_visitante = db.query(Equipo).filter(Equipo.id_equipo == partido.id_equipo_visitante).first()

    if not equipo_local or not equipo_visitante:
        raise ValueError("Uno o ambos equipos no existen")

    # Verificar si el usuario es admin de la liga
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol
    es_admin = db.query(UsuarioRol).join(
        Rol, UsuarioRol.id_rol == Rol.id_rol
    ).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == partido.id_liga,
        Rol.nombre == "admin"
    ).first() is not None

    es_entrenador_o_delegado = (
        usuario_id == equipo_local.id_entrenador or
        usuario_id == equipo_local.id_delegado or
        usuario_id == equipo_visitante.id_entrenador or
        usuario_id == equipo_visitante.id_delegado
    )
    if not es_admin and not es_entrenador_o_delegado:
        raise ValueError("Solo el administrador, entrenador o delegado puede iniciar el partido")

    # Validar que la fecha/hora del partido haya llegado
    # Usar timezone.utc para comparar correctamente con partido.fecha (DateTime con timezone)
    ahora = datetime.now(timezone.utc)
    if partido.fecha > ahora:
        raise ValueError("La fecha/hora del partido aún no ha llegado")

    # Validar convocatoria de ambos equipos (usar convocatoria_partido, no alineacion_partido)
    for id_equipo in [partido.id_equipo_local, partido.id_equipo_visitante]:
        # Obtener titulares convocados (11 jugadores) - hacer join con Jugador para filtrar por equipo
        from sqlalchemy.orm import joinedload
        convocados_titulares = db.query(ConvocatoriaPartido).join(
            Jugador, ConvocatoriaPartido.id_jugador == Jugador.id_jugador
        ).filter(
            ConvocatoriaPartido.id_partido == partido_id,
            Jugador.id_equipo == id_equipo,
            ConvocatoriaPartido.es_titular == True
        ).all()

        if len(convocados_titulares) != 11:
            raise ValueError(f"El equipo {id_equipo} debe tener exactamente 11 titulares en la convocatoria, tiene {len(convocados_titulares)}")

        # Validar al menos 1 portero entre los titulares convocados
        ids_jugadores = [c.id_jugador for c in convocados_titulares]
        jugadores = db.query(Jugador).filter(
            Jugador.id_jugador.in_(ids_jugadores),
            Jugador.posicion.ilike("%portero%")
        ).all()

        if len(jugadores) < 1:
            raise ValueError(f"El equipo {id_equipo} debe tener al menos 1 portero entre los titulares")

    # Cambiar estado a 'en_juego'
    partido.estado = "en_juego"

    # Forzar la carga de las relaciones de equipos para evitar InvalidRequestError en notificaciones
    db.refresh(partido, attribute_names=['equipo_local', 'equipo_visitante'])

    # Inicializar estados de los jugadores
    _inicializar_estados_jugadores(db, partido, [partido.id_equipo_local, partido.id_equipo_visitante])

    db.commit()
    db.refresh(partido)

    # Notificar solo a los equipos involucrados (jugadores, entrenador, delegado)
    notificar_equipo(
        db=db,
        id_equipo=partido.id_equipo_local,
        tipo="partido_iniciado",
        titulo="Partido Iniciado",
        mensaje=f"¡Comienza el partido contra {partido.equipo_visitante.nombre}!",
        id_referencia=partido.id_partido,
        tipo_referencia="partido"
    )

    notificar_equipo(
        db=db,
        id_equipo=partido.id_equipo_visitante,
        tipo="partido_iniciado",
        titulo="Partido Iniciado",
        mensaje=f"¡Comienza el partido contra {partido.equipo_local.nombre}!",
        id_referencia=partido.id_partido,
        tipo_referencia="partido"
    )

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

        # Obtener titulares de la convocatoria (join con Jugador para filtrar por equipo)
        titulares_convocatoria = db.query(ConvocatoriaPartido).join(
            Jugador, ConvocatoriaPartido.id_jugador == Jugador.id_jugador
        ).filter(
            ConvocatoriaPartido.id_partido == partido.id_partido,
            Jugador.id_equipo == id_equipo,
            ConvocatoriaPartido.es_titular == True
        ).all()
        ids_titulares = [c.id_jugador for c in titulares_convocatoria]

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

    # Validación MVP - Verificar que ambos equipos tienen jugadores válidos en campo
    # 1. Validar mínimo 5 jugadores por equipo (mínimo reglamentario)
    for id_equipo in [partido.id_equipo_local, partido.id_equipo_visitante]:
        # Obtener jugadores que estuvieron "jugando" en algún momento del partido
        jugadores_en_campo = db.query(EstadoJugadorPartido).filter(
            EstadoJugadorPartido.id_partido == partido_id,
            EstadoJugadorPartido.id_equipo == id_equipo,
            EstadoJugadorPartido.estado == "jugando"
        ).all()

        if len(jugadores_en_campo) < 5:
            raise ValueError(f"El equipo {id_equipo} debe tener al menos 5 jugadores en campo para finalizar el partido, solo tiene {len(jugadores_en_campo)}")

        # 2. Validar que los jugadores existen y pertenecen al equipo correcto
        ids_jugadores = [e.id_jugador for e in jugadores_en_campo]
        jugadores_validos = db.query(Jugador).filter(
            Jugador.id_jugador.in_(ids_jugadores),
            Jugador.id_equipo == id_equipo,
            Jugador.activo == True
        ).all()

        if len(jugadores_validos) != len(jugadores_en_campo):
            raise ValueError(f"El equipo {id_equipo} tiene jugadores no válidos o que no pertenecen al equipo")

    # 3. Validar que el jugador MVP estuvo convocado al partido
    convocatoria_mvp = db.query(ConvocatoriaPartido).filter(
        ConvocatoriaPartido.id_partido == partido_id,
        ConvocatoriaPartido.id_jugador == datos.id_mvp
    ).first()

    if not convocatoria_mvp:
        raise ValueError("El jugador seleccionado como MVP no estuvo convocado en este partido")

    # 4. Validar que el MVP pertenece a uno de los equipos del partido
    mvp_pertenece_equipo = db.query(Jugador).filter(
        Jugador.id_jugador == datos.id_mvp,
        Jugador.id_equipo.in_([partido.id_equipo_local, partido.id_equipo_visitante])
    ).first()

    if not mvp_pertenece_equipo:
        raise ValueError("El jugador MVP no pertenece a ninguno de los equipos del partido")

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

    # Notificar solo a los equipos involucrados con el resultado final
    notificar_equipo(
        db=db,
        id_equipo=partido.id_equipo_local,
        tipo="partido_finalizado",
        titulo="Partido Finalizado",
        mensaje=f"{partido.equipo_local.nombre} {partido.goles_local} - {partido.goles_visitante} {partido.equipo_visitante.nombre}",
        id_referencia=partido.id_partido,
        tipo_referencia="partido"
    )

    notificar_equipo(
        db=db,
        id_equipo=partido.id_equipo_visitante,
        tipo="partido_finalizado",
        titulo="Partido Finalizado",
        mensaje=f"{partido.equipo_visitante.nombre} {partido.goles_visitante} - {partido.goles_local} {partido.equipo_local.nombre}",
        id_referencia=partido.id_partido,
        tipo_referencia="partido"
    )

    return partido
