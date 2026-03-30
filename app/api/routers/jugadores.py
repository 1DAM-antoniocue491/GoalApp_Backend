# app/api/routers/jugadores.py
"""
Router de Jugadores - Gestión de jugadores de fútbol.
Endpoints para crear, listar, actualizar y eliminar jugadores del sistema.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.jugador import JugadorCreate, JugadorUpdate, JugadorResponse
from app.api.services.jugador_service import (
    crear_jugador,
    obtener_jugadores,
    obtener_jugador_por_id,
    actualizar_jugador,
    eliminar_jugador
)

# Configuración del router
router = APIRouter(
    prefix="/jugadores",  # Base path: /api/v1/jugadores
    tags=["Jugadores"]  # Agrupación en documentación
)

@router.post("/", response_model=JugadorResponse, dependencies=[Depends(require_role("admin"))])
def crear_jugador_router(jugador: JugadorCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo jugador.
    
    Registra un nuevo jugador en el sistema con su información personal,
    física y del equipo al que pertenece.
    
    Parámetros:
        - jugador (JugadorCreate): Datos del jugador (nombre, edad, posición, equipo_id, etc.)
        - db (Session): Sesión de base de datos
    
    Returns:
        JugadorResponse: Información del jugador creado con su ID asignado
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_jugador(db, jugador)

@router.get("/", response_model=list[JugadorResponse])
def listar_jugadores(db: Session = Depends(get_db)):
    """
    Listar todos los jugadores.
    
    Obtiene la lista completa de jugadores registrados en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[JugadorResponse]: Lista de todos los jugadores
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_jugadores(db)

@router.get("/{jugador_id}", response_model=JugadorResponse)
def obtener_jugador_router(jugador_id: int, db: Session = Depends(get_db)):
    """
    Obtener un jugador por su ID.
    
    Devuelve la información detallada de un jugador específico.
    
    Parámetros:
        - jugador_id (int): ID único del jugador (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        JugadorResponse: Información completa del jugador
    
    Requiere autenticación: No
    Roles permitidos: Público
    
    Raises:
        HTTPException 404: Si el jugador no existe
    """
    jugador = obtener_jugador_por_id(db, jugador_id)
    # Validar que el jugador exista
    if not jugador:
        raise HTTPException(404, "Jugador no encontrado")
    return jugador

@router.put("/{jugador_id}", response_model=JugadorResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_jugador_router(jugador_id: int, datos: JugadorUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de un jugador.
    
    Modifica los datos de un jugador existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - jugador_id (int): ID del jugador a actualizar (path parameter)
        - datos (JugadorUpdate): Campos del jugador a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        JugadorResponse: Información actualizada del jugador
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_jugador(db, jugador_id, datos)

@router.delete("/{jugador_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_jugador_router(jugador_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un jugador.
    
    Elimina un jugador del sistema. Esta acción puede afectar registros relacionados
    como eventos de partido y posiciones en formaciones.
    
    Parámetros:
        - jugador_id (int): ID del jugador a eliminar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_jugador(db, jugador_id)
    return {"mensaje": "Jugador eliminado correctamente"}
