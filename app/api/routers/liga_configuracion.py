# app/api/routers/liga_configuracion.py
"""
Router de Configuración de Liga - Gestión de parámetros de liga.
Endpoints para configurar y obtener la configuración de cada liga.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.liga_configuracion import (
    LigaConfiguracionCreate,
    LigaConfiguracionUpdate,
    LigaConfiguracionResponse
)
from app.api.services.liga_configuracion_service import (
    obtener_configuracion,
    crear_configuracion,
    actualizar_configuracion
)
from app.api.services.liga_service import obtener_liga_por_id

# Configuración del router
router = APIRouter(
    prefix="/ligas",  # Base path: /api/v1/ligas
    tags=["Configuración de Liga"]
)


@router.get("/{liga_id}/configuracion", response_model=LigaConfiguracionResponse)
def obtener_configuracion_liga(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener la configuración de una liga.

    Devuelve los parámetros de configuración de una liga específica:
    - Hora habitual de partidos
    - Máximo de equipos
    - Mínimo de jugadores por equipo
    - Mínimo de partidos entre equipos

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        LigaConfiguracionResponse: Configuración de la liga

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 404: Si la liga no existe o no tiene configuración
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    configuracion = obtener_configuracion(db, liga_id)
    if not configuracion:
        raise HTTPException(status_code=404, detail="La liga no tiene configuración")

    return configuracion


@router.post("/{liga_id}/configuracion", response_model=LigaConfiguracionResponse, dependencies=[Depends(require_role("admin"))])
def crear_configuracion_liga(
    liga_id: int,
    datos: LigaConfiguracionCreate,
    db: Session = Depends(get_db)
):
    """
    Crear la configuración de una liga.

    Establece los parámetros de configuración para una liga recién creada.
    Solo se puede crear una configuración por liga.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - datos (LigaConfiguracionCreate): Datos de la configuración
        - db (Session): Sesión de base de datos

    Returns:
        LigaConfiguracionResponse: Configuración creada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga no existe
        HTTPException 400: Si la liga ya tiene configuración
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    try:
        configuracion = crear_configuracion(db, liga_id, datos)
        return configuracion
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{liga_id}/configuracion", response_model=LigaConfiguracionResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_configuracion_liga(
    liga_id: int,
    datos: LigaConfiguracionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar la configuración de una liga.

    Modifica los parámetros de configuración de una liga existente.
    Solo se actualizan los campos proporcionados en el body.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - datos (LigaConfiguracionUpdate): Campos a actualizar
        - db (Session): Sesión de base de datos

    Returns:
        LigaConfiguracionResponse: Configuración actualizada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga o configuración no existe
    """
    # Verificar que la liga existe
    liga = obtener_liga_por_id(db, liga_id)
    if not liga:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    try:
        configuracion = actualizar_configuracion(db, liga_id, datos)
        return configuracion
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))