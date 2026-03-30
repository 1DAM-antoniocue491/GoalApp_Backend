# app/api/routers/partidos.py
"""
Router de Partidos - Gestión de partidos de fútbol.
Endpoints para crear, listar, actualizar y eliminar partidos del sistema.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.partido import PartidoCreate, PartidoUpdate, PartidoResponse
from app.api.services.partido_service import (
    crear_partido,
    obtener_partidos,
    obtener_partido_por_id,
    actualizar_partido,
    eliminar_partido
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
def listar_partidos(db: Session = Depends(get_db)):
    """
    Listar todos los partidos.
    
    Obtiene la lista completa de partidos registrados en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[PartidoResponse]: Lista de todos los partidos
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_partidos(db)

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
