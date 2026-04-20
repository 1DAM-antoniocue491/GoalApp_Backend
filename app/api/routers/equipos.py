# app/api/routers/equipos.py
"""
Router de Equipos - Gestión de equipos de fútbol.
Endpoints para crear, listar, actualizar y eliminar equipos.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoResponse, EquipoRendimientoResponse
from app.api.services.equipo_service import (
    crear_equipo,
    obtener_equipos,
    obtener_equipo_por_id,
    actualizar_equipo,
    eliminar_equipo,
    obtener_equipos_con_rendimiento
)

# Configuración del router
router = APIRouter(
    prefix="/equipos",  # Base path: /api/v1/equipos
    tags=["Equipos"]  # Agrupación en documentación
)

@router.post("/", response_model=EquipoResponse, dependencies=[Depends(require_role("admin"))])
def crear_equipo_router(equipo: EquipoCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo equipo.
    
    Registra un nuevo equipo en el sistema con su información básica.
    
    Parámetros:
        - equipo (EquipoCreate): Datos del equipo a crear (nombre, escudo, ciudad, etc.)
        - db (Session): Sesión de base de datos
    
    Returns:
        EquipoResponse: Información del equipo creado con su ID asignado
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_equipo(db, equipo)

@router.get("/", response_model=list[EquipoResponse])
def listar_equipos(liga_id: int = None, db: Session = Depends(get_db)):
    """
    Listar todos los equipos, opcionalmente filtrados por liga.

    Obtiene la lista completa de equipos registrados en el sistema.
    Si se proporciona liga_id, solo devuelve los equipos de esa liga.

    Parámetros:
        - liga_id (int, optional): ID de la liga para filtrar (query parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[EquipoResponse]: Lista de equipos (filtrados por liga si se proporciona)

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_equipos(db, liga_id)

@router.get("/{equipo_id}", response_model=EquipoResponse)
def obtener_equipo_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener un equipo por su ID.

    Devuelve la información detallada de un equipo específico.

    Parámetros:
        - equipo_id (int): ID único del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        EquipoResponse: Información completa del equipo

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 404: Si el equipo no existe
    """
    equipo = obtener_equipo_por_id(db, equipo_id)
    # Validar que el equipo exista
    if not equipo:
        raise HTTPException(404, "Equipo no encontrado")
    return equipo


@router.get("/ligas/{liga_id}/rendimiento", response_model=list[EquipoRendimientoResponse])
def listar_equipos_rendimiento(liga_id: int, db: Session = Depends(get_db)):
    """
    Listar todos los equipos de una liga con sus estadísticas de rendimiento.

    Obtiene la lista de equipos de una liga específica junto con sus estadísticas
    de victorias, empates y derrotas calculadas a partir de los partidos finalizados.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[EquipoRendimientoResponse]: Lista de equipos con sus estadísticas,
                                          ordenada por porcentaje de victorias descendente

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_equipos_con_rendimiento(db, liga_id)

@router.put("/{equipo_id}", response_model=EquipoResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_equipo_router(equipo_id: int, datos: EquipoUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de un equipo.
    
    Modifica los datos de un equipo existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - equipo_id (int): ID del equipo a actualizar (path parameter)
        - datos (EquipoUpdate): Campos del equipo a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        EquipoResponse: Información actualizada del equipo
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_equipo(db, equipo_id, datos)

@router.delete("/{equipo_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_equipo_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un equipo.
    
    Elimina un equipo del sistema. Esta acción puede afectar registros relacionados
    como jugadores, partidos y formaciones.
    
    Parámetros:
        - equipo_id (int): ID del equipo a eliminar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_equipo(db, equipo_id)
    return {"mensaje": "Equipo eliminado correctamente"}
