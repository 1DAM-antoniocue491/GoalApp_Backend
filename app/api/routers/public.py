# app/api/routers/public.py
"""
Router Público - Endpoints accesibles sin autenticación.
Información pública de ligas, equipos, partidos y clasificación.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.services.liga_service import obtener_liga_por_id, obtener_clasificacion
from app.api.services.partido_service import obtener_partidos
from app.schemas.liga import LigaResponse
from app.schemas.clasificacion import ClasificacionItem
from app.schemas.partido import PartidoResponse

# Configuración del router
router = APIRouter(
    prefix="/public",
    tags=["Público"]
)


@router.get("/ligas/{liga_id}", response_model=LigaResponse, summary="Obtener liga pública")
def obtener_liga_publica(
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene información pública de una liga.

    Parámetros:
        - liga_id (int): ID de la liga
        - db (Session): Sesión de base de datos

    Returns:
        LigaResponse: Información de la liga

    Requiere autenticación: No
    """
    from fastapi import HTTPException
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise HTTPException(404, "Liga no encontrada")
    return liga


@router.get("/ligas/{liga_id}/clasificacion", response_model=list[ClasificacionItem], summary="Obtener clasificación pública")
def obtener_clasificacion_publica(
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la clasificación pública de una liga.

    Devuelve la tabla de posiciones ordenada por puntos, diferencia de goles y goles a favor.
    Solo considera partidos finalizados.

    Parámetros:
        - liga_id (int): ID de la liga
        - db (Session): Sesión de base de datos

    Returns:
        List[ClasificacionItem]: Clasificación ordenada

    Requiere autenticación: No
    """
    from fastapi import HTTPException
    try:
        return obtener_clasificacion(db, liga_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/ligas/{liga_id}/partidos", response_model=list[PartidoResponse], summary="Obtener partidos de una liga")
def obtener_partidos_publicos(
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los partidos públicos de una liga.

    Devuelve todos los partidos de una liga, incluyendo programados, en juego y finalizados.

    Parámetros:
        - liga_id (int): ID de la liga
        - db (Session): Sesión de base de datos

    Returns:
        List[PartidoResponse]: Lista de partidos

    Requiere autenticación: No
    """
    from fastapi import HTTPException
    from app.models.partido import Partido

    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    # Obtener partidos de la liga
    partidos = db.query(Partido).filter(Partido.id_liga == liga_id).all()
    return partidos


@router.get("/ligas/{liga_id}/jornada/{jornada}", response_model=list[PartidoResponse], summary="Obtener partidos de una jornada")
def obtener_jornada_publica(
    liga_id: int,
    jornada: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los partidos de una jornada específica de una liga.

    Nota: La jornada se calcula por el orden de fecha de los partidos.
    Una jornada es un conjunto de partidos que se juegan en la misma fecha aproximada.

    Parámetros:
        - liga_id (int): ID de la liga
        - jornada (int): Número de jornada (1-based)
        - db (Session): Sesión de base de datos

    Returns:
        List[PartidoResponse]: Lista de partidos de la jornada

    Requiere autenticación: No
    """
    from fastapi import HTTPException
    from app.models.partido import Partido
    from sqlalchemy import func

    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    # Obtener todas las fechas únicas de partidos ordenadas
    fechas = db.query(func.date(func.timezone('UTC', Partido.fecha))).filter(
        Partido.id_liga == liga_id
    ).distinct().order_by(Partido.fecha).all()

    fechas_ordenadas = [f[0] for f in fechas]

    if jornada < 1 or jornada > len(fechas_ordenadas):
        raise HTTPException(404, f"Jornada {jornada} no encontrada")

    # Obtener partidos de la jornada
    fecha_jornada = fechas_ordenadas[jornada - 1]
    partidos = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        func.date(func.timezone('UTC', Partido.fecha)) == fecha_jornada
    ).all()

    return partidos