# app/api/routers/ligas.py
"""
Router de Ligas - Gestión de ligas y competiciones.
Endpoints para crear, listar, actualizar y eliminar ligas de fútbol.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.liga import LigaCreate, LigaUpdate, LigaResponse
from app.schemas.clasificacion import ClasificacionItem
from app.api.services.liga_service import (
    crear_liga,
    obtener_ligas,
    obtener_liga_por_id,
    actualizar_liga,
    eliminar_liga,
    obtener_clasificacion,
    reactivar_liga,
    desactivar_liga
)

# Configuración del router
router = APIRouter(
    prefix="/ligas",  # Base path: /api/v1/ligas
    tags=["Ligas"]  # Agrupación en documentación
)

@router.post("/", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def crear_liga_router(liga: LigaCreate, db: Session = Depends(get_db)):
    """
    Crear una nueva liga.
    
    Registra una nueva liga o competición en el sistema con su información básica.
    
    Parámetros:
        - liga (LigaCreate): Datos de la liga (nombre, país, temporada, etc.)
        - db (Session): Sesión de base de datos
    
    Returns:
        LigaResponse: Información de la liga creada con su ID asignado
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_liga(db, liga)

@router.get("/", response_model=list[LigaResponse])
def listar_ligas(db: Session = Depends(get_db)):
    """
    Listar todas las ligas.
    
    Obtiene la lista completa de ligas registradas en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[LigaResponse]: Lista de todas las ligas
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_ligas(db)

@router.get("/{liga_id}", response_model=LigaResponse)
def obtener_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener una liga por su ID.
    
    Devuelve la información detallada de una liga específica.
    
    Parámetros:
        - liga_id (int): ID único de la liga (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        LigaResponse: Información completa de la liga
    
    Requiere autenticación: No
    Roles permitidos: Público
    
    Raises:
        HTTPException 404: Si la liga no existe
    """
    liga = obtener_liga_por_id(db, liga_id)
    # Validar que la liga exista
    if not liga:
        raise HTTPException(404, "Liga no encontrada")
    return liga

@router.put("/{liga_id}", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_liga_router(liga_id: int, datos: LigaUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de una liga.
    
    Modifica los datos de una liga existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - liga_id (int): ID de la liga a actualizar (path parameter)
        - datos (LigaUpdate): Campos de la liga a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        LigaResponse: Información actualizada de la liga
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_liga(db, liga_id, datos)

@router.delete("/{liga_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Eliminar una liga.
    
    Elimina una liga del sistema. Esta acción puede afectar registros relacionados
    como partidos y equipos asociados a la liga.
    
    Parámetros:
        - liga_id (int): ID de la liga a eliminar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_liga(db, liga_id)
    return {"mensaje": "Liga eliminada"}

@router.get("/{liga_id}/clasificacion", response_model=list[ClasificacionItem])
def obtener_clasificacion_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener la clasificación de una liga.

    Calcula y devuelve la tabla de clasificación ordenada por:
    1. Puntos (descendente)
    2. Diferencia de goles (descendente)
    3. Goles a favor (descendente)

    Solo considera partidos con estado "finalizado".

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[ClasificacionItem]: Lista de equipos con sus estadísticas ordenados por posición

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 404: Si la liga no existe
    """
    try:
        return obtener_clasificacion(db, liga_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.put("/{liga_id}/reactivar", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def reactivar_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Reactivar una liga inactiva.

    Cambia el estado de una liga de inactiva a activa. Solo los administradores
    pueden realizar esta acción.

    Parámetros:
        - liga_id (int): ID de la liga a reactivar (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        LigaResponse: Información de la liga reactivada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga no existe
        HTTPException 400: Si la liga ya está activa
    """
    try:
        return reactivar_liga(db, liga_id)
    except ValueError as e:
        if "no encontrada" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))

@router.put("/{liga_id}/desactivar", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def desactivar_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Desactivar una liga activa.

    Cambia el estado de una liga de activa a inactiva. Solo los administradores
    pueden realizar esta acción. Una liga inactiva no permite crear nuevos partidos
    ni modificar datos.

    Parámetros:
        - liga_id (int): ID de la liga a desactivar (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        LigaResponse: Información de la liga desactivada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga no existe
        HTTPException 400: Si la liga ya está inactiva
    """
    try:
        return desactivar_liga(db, liga_id)
    except ValueError as e:
        if "no encontrada" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))
