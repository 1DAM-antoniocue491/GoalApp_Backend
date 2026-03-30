# app/api/routers/equipos.py
"""
Router de Equipos - Gestión de equipos de fútbol.
Endpoints para crear, listar, actualizar y eliminar equipos.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoResponse
from app.api.services.equipo_service import (
    crear_equipo,
    obtener_equipos,
    obtener_equipo_por_id,
    actualizar_equipo,
    eliminar_equipo
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
def listar_equipos(db: Session = Depends(get_db)):
    """
    Listar todos los equipos.
    
    Obtiene la lista completa de equipos registrados en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[EquipoResponse]: Lista de todos los equipos
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_equipos(db)

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
