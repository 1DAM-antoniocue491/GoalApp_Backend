# app/api/routers/partidos.py
"""
Router de Partidos - Gestión de partidos de fútbol.
Endpoints para crear, listar, actualizar y eliminar partidos del sistema.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.partido import PartidoCreate, PartidoUpdate, PartidoResponse, CalendarCreateRequest, CalendarCreateResponse
from app.api.services.partido_service import (
    crear_partido,
    obtener_partidos,
    obtener_partido_por_id,
    actualizar_partido,
    eliminar_partido,
    obtener_partidos_con_equipos,
    obtener_partidos_por_jornada,
    obtener_partidos_proximos,
    obtener_partidos_en_vivo,
    crear_calendario
)

# Configuración del router
router = APIRouter(
    prefix="/partidos",  # Base path: /api/v1/partidos
    tags=["Partidos"]  # Agrupación en documentación
)

@router.post("/", response_model=PartidoResponse, dependencies=[Depends(require_role("admin"))])
def crear_partido_router(partido: PartidoCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo partido.
    
    Registra un nuevo partido en el sistema con información de equipos, fecha,
    hora, estadio y liga.
    
    Parámetros:
        - partido (PartidoCreate): Datos del partido (equipo_local_id, equipo_visitante_id, fecha, etc.)
        - db (Session): Sesión de base de datos
    
    Returns:
        PartidoResponse: Información del partido creado con su ID asignado
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_partido(db, partido)

@router.get("/", response_model=list[PartidoResponse])
def listar_partidos(liga_id: int | None = Query(None, description="Filtrar por ID de liga"), db: Session = Depends(get_db)):
    """
    Listar todos los partidos, opcionalmente filtrados por liga.

    Obtiene la lista completa de partidos registrados en el sistema.
    Si se proporciona liga_id, solo devuelve los partidos de esa liga.

    Parámetros:
        - liga_id (int, optional): ID de la liga para filtrar (query parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[PartidoResponse]: Lista de partidos (filtrados por liga si se proporciona)

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_partidos(db, liga_id)


# ENDPOINTS ESPECÍFICOS (deben ir ANTES de /{partido_id} para evitar conflictos)
# ============================================================================

@router.get("/ligas/{liga_id}/con-equipos", response_model=list)
def listar_partidos_con_equipos(liga_id: int, db: Session = Depends(get_db)):
    """
    Listar todos los partidos de una liga con información de equipos.

    Obtiene los partidos de una liga específica incluyendo nombres y escudos
    de los equipos local y visitante.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[dict]: Lista de partidos con información completa de equipos

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_partidos_con_equipos(db, liga_id)


@router.get("/ligas/{liga_id}/jornadas", response_model=list)
def listar_partidos_por_jornada(liga_id: int, db: Session = Depends(get_db)):
    """
    Listar partidos de una liga agrupados por jornada.

    Obtiene los partidos de una liga específica organizados por número de jornada.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[dict]: Lista de jornadas con sus partidos

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_partidos_por_jornada(db, liga_id)


@router.get("/proximos", response_model=list)
def listar_partidos_proximos(limit: int = 10, db: Session = Depends(get_db)):
    """
    Listar próximos partidos programados.

    Obtiene los próximos partidos que están en estado 'Programado',
    ordenados por fecha ascendente.

    Parámetros:
        - limit (int, optional): Número máximo de partidos a devolver (default: 10)
        - db (Session): Sesión de base de datos

    Returns:
        List[dict]: Lista de próximos partidos con información de equipos

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_partidos_proximos(db, limit)


@router.get("/en-vivo", response_model=list)
def listar_partidos_en_vivo(db: Session = Depends(get_db)):
    """
    Listar partidos que están en vivo.

    Obtiene los partidos que están en estado 'En Juego'.

    Parámetros:
        - db (Session): Sesión de base de datos

    Returns:
        List[dict]: Lista de partidos en vivo con información de equipos

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_partidos_en_vivo(db)


@router.post("/ligas/{liga_id}/crear-calendario", response_model=CalendarCreateResponse, dependencies=[Depends(require_role("admin"))])
def crear_calendario_router(liga_id: int, config: CalendarCreateRequest, db: Session = Depends(get_db)):
    """
    Crear calendario automático para una liga.

    Genera todos los partidos de la liga basándose en la configuración proporcionada:
    - Tipo de calendario (solo ida o ida y vuelta)
    - Fecha de inicio
    - Días de partido seleccionados
    - Hora de los partidos

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - config (CalendarCreateRequest): Configuración del calendario
        - db (Session): Sesión de base de datos

    Returns:
        CalendarCreateResponse: Mensaje de confirmación y número de partidos creados

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_calendario(db, liga_id, config)


# ENDPOINTS GENÉRICOS CON ID (deben ir DESPUÉS de los específicos)
# ============================================================================

@router.get("/{partido_id}", response_model=PartidoResponse)
def obtener_partido_router(partido_id: int, db: Session = Depends(get_db)):
    """
    Obtener un partido por su ID.

    Devuelve la información detallada de un partido específico, incluyendo
    equipos, resultado, estadio y eventos.

    Parámetros:
        - partido_id (int): ID único del partido (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        PartidoResponse: Información completa del partido

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 404: Si el partido no existe
    """
    partido = obtener_partido_por_id(db, partido_id)
    # Validar que el partido exista
    if not partido:
        raise HTTPException(404, "Partido no encontrado")
    return partido


@router.put("/{partido_id}", response_model=PartidoResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_partido_router(partido_id: int, datos: PartidoUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de un partido.

    Modifica los datos de un partido existente. Solo se actualizan los campos
    proporcionados en el body de la petición (resultado, fecha, estadio, etc.).

    Parámetros:
        - partido_id (int): ID del partido a actualizar (path parameter)
        - datos (PartidoUpdate): Campos del partido a modificar
        - db (Session): Sesión de base de datos

    Returns:
        PartidoResponse: Información actualizada del partido

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_partido(db, partido_id, datos)


@router.delete("/{partido_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_partido_router(partido_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un partido.

    Elimina un partido del sistema. Esta acción puede afectar registros relacionados
    como eventos, formaciones y estadísticas.

    Parámetros:
        - partido_id (int): ID del partido a eliminar (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_partido(db, partido_id)
    return {"mensaje": "Partido eliminado correctamente"}
