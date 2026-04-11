# app/api/routers/alineaciones.py
"""
Router de Alineaciones - Gestión de alineaciones de jugadores en partidos.
Endpoints para crear, obtener, actualizar y eliminar alineaciones.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, get_current_user
from app.schemas.alineacion import (
    AlineacionCreate,
    AlineacionUpdate,
    AlineacionResponse,
    AlineacionBulkCreate,
    AlineacionEquipoResponse
)
from app.api.services.alineacion_service import (
    crear_alineacion,
    crear_alineaciones_bulk,
    obtener_alineacion_por_id,
    obtener_alineaciones_partido,
    obtener_alineacion_equipo,
    actualizar_alineacion,
    eliminar_alineacion,
    eliminar_alineaciones_partido
)

# Configuración del router
router = APIRouter(
    prefix="/alineaciones",
    tags=["Alineaciones"]
)


@router.post("/", response_model=AlineacionResponse, summary="Crear alineación individual")
def crear_alineacion_router(
    datos: AlineacionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crea una alineación individual para un partido.

    Asigna un jugador a una posición específica en un partido.

    Parámetros:
        - datos (AlineacionCreate): Datos de la alineación
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        AlineacionResponse: Información de la alineación creada

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate

    Raises:
        HTTPException 400: Si el jugador ya está alineado
        HTTPException 404: Si el partido, jugador o posición no existen
    """
    # Verificar permisos: admin, coach o delegate
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para crear alineaciones")

    try:
        return crear_alineacion(db, datos)
    except ValueError as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.post("/bulk", response_model=List[AlineacionResponse], summary="Crear múltiples alineaciones")
def crear_alineaciones_bulk_router(
    datos: AlineacionBulkCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crea múltiples alineaciones para un partido en una sola operación.

    Elimina las alineaciones existentes y crea las nuevas.

    Parámetros:
        - datos (AlineacionBulkCreate): Datos de las alineaciones (id_partido + lista)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        List[AlineacionResponse]: Lista de alineaciones creadas

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate

    Raises:
        HTTPException 400: Si hay más de 11 titulares o errores de validación
        HTTPException 404: Si el partido no existe
    """
    # Verificar permisos: admin, coach o delegate
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para crear alineaciones")

    try:
        return crear_alineaciones_bulk(db, datos)
    except ValueError as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get("/{id_alineacion}", response_model=AlineacionResponse, summary="Obtener alineación por ID")
def obtener_alineacion_router(
    id_alineacion: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene una alineación por su ID.

    Parámetros:
        - id_alineacion (int): ID de la alineación
        - db (Session): Sesión de base de datos

    Returns:
        AlineacionResponse: Información de the alineación

    Requiere autenticación: No

    Raises:
        HTTPException 404: Si la alineación no existe
    """
    alineacion = obtener_alineacion_por_id(db, id_alineacion)
    if not alineacion:
        raise HTTPException(404, f"Alineación con ID {id_alineacion} no encontrada")
    return alineacion


@router.get("/partido/{id_partido}", response_model=List[AlineacionResponse], summary="Obtener alineaciones de un partido")
def obtener_alineaciones_partido_router(
    id_partido: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las alineaciones de un partido.

    Parámetros:
        - id_partido (int): ID del partido
        - db (Session): Sesión de base de datos

    Returns:
        List[AlineacionResponse]: Lista de alineaciones del partido

    Requiere autenticación: No

    Raises:
        HTTPException 404: Si el partido no existe
    """
    try:
        return obtener_alineaciones_partido(db, id_partido)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get(
    "/partido/{id_partido}/equipo/{id_equipo}",
    response_model=AlineacionEquipoResponse,
    summary="Obtener alineación de un equipo en un partido"
)
def obtener_alineacion_equipo_router(
    id_partido: int,
    id_equipo: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la alineación de un equipo específico en un partido.

    Devuelve titulares y suplentes con información detallada.

    Parámetros:
        - id_partido (int): ID del partido
        - id_equipo (int): ID del equipo
        - db (Session): Sesión de base de datos

    Returns:
        AlineacionEquipoResponse: Alineación del equipo

    Requiere autenticación: No

    Raises:
        HTTPException 404: Si el partido o equipo no existen
        HTTPException 400: Si el equipo no participa en el partido
    """
    try:
        return obtener_alineacion_equipo(db, id_partido, id_equipo)
    except ValueError as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.put("/{id_alineacion}", response_model=AlineacionResponse, summary="Actualizar alineación")
def actualizar_alineacion_router(
    id_alineacion: int,
    datos: AlineacionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Actualiza una alineación existente.

    Permite cambiar la posición o el estado de titular.

    Parámetros:
        - id_alineacion (int): ID de la alineación
        - datos (AlineacionUpdate): Datos a actualizar
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        AlineacionResponse: Alineación actualizada

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate

    Raises:
        HTTPException 404: Si la alineación o posición no existen
    """
    # Verificar permisos
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para actualizar alineaciones")

    try:
        return actualizar_alineacion(db, id_alineacion, datos)
    except ValueError as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.delete("/{id_alineacion}", summary="Eliminar alineación individual")
def eliminar_alineacion_router(
    id_alineacion: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Elimina una alineación individual.

    Parámetros:
        - id_alineacion (int): ID de la alineación
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate

    Raises:
        HTTPException 404: Si la alineación no existe
    """
    # Verificar permisos
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para eliminar alineaciones")

    try:
        eliminar_alineacion(db, id_alineacion)
        return {"mensaje": f"Alineación con ID {id_alineacion} eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/partido/{id_partido}", summary="Eliminar todas las alineaciones de un partido")
def eliminar_alineaciones_partido_router(
    id_partido: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Elimina todas las alineaciones de un partido.

    Parámetros:
        - id_partido (int): ID del partido
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate

    Raises:
        HTTPException 404: Si el partido no existe
    """
    # Verificar permisos
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para eliminar alineaciones")

    try:
        eliminar_alineaciones_partido(db, id_partido)
        return {"mensaje": f"Alineaciones del partido {id_partido} eliminadas correctamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))