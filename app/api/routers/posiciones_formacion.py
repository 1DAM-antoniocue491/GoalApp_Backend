# app/api/routers/posiciones_formacion.py
"""
Router de Posiciones de Formación - Gestión de posiciones genéricas del campo.
Endpoints para CRUD de posiciones (Portero, Defensa, Mediocentro, etc.).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, require_role
from app.models.posicion_formacion import PosicionFormacion
from app.schemas.posicion_formacion import (
    PosicionFormacionCreate,
    PosicionFormacionUpdate,
    PosicionFormacionResponse
)
from app.api.services.posicion_formacion_service import (
    crear_posicion_formacion,
    obtener_posiciones_formacion,
    obtener_posicion_formacion_por_id,
    actualizar_posicion_formacion,
    eliminar_posicion_formacion
)

# Configuración del router
router = APIRouter(
    prefix="/posiciones-formacion",
    tags=["Posiciones de Formación"]
)


@router.post("/", response_model=PosicionFormacionResponse, summary="Crear posición de formación")
def crear_posicion_router(
    datos: PosicionFormacionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Crea una nueva posición de formación.

    Las posiciones son genéricas del campo de fútbol (Portero, Defensa Central, etc.)
    y se utilizan en las alineaciones de los partidos.

    Parámetros:
        - datos (PosicionFormacionCreate): Datos de la posición (nombre, descripcion)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        PosicionFormacionResponse: Información de la posición creada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 400: Si ya existe una posición con el mismo nombre
    """
    try:
        return crear_posicion_formacion(db, datos)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/", response_model=List[PosicionFormacionResponse], summary="Listar posiciones de formación")
def listar_posiciones_router(db: Session = Depends(get_db)):
    """
    Obtiene todas las posiciones de formación registradas.

    Devuelve la lista de posiciones ordenadas alfabéticamente por nombre.

    Parámetros:
        - db (Session): Sesión de base de datos

    Returns:
        List[PosicionFormacionResponse]: Lista de posiciones

    Requiere autenticación: No
    """
    return obtener_posiciones_formacion(db)


@router.get("/{id_posicion}", response_model=PosicionFormacionResponse, summary="Obtener posición por ID")
def obtener_posicion_router(
    id_posicion: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene una posición de formación por su ID.

    Parámetros:
        - id_posicion (int): ID de la posición
        - db (Session): Sesión de base de datos

    Returns:
        PosicionFormacionResponse: Información de la posición

    Requiere autenticación: No

    Raises:
        HTTPException 404: Si la posición no existe
    """
    posicion = obtener_posicion_formacion_por_id(db, id_posicion)
    if not posicion:
        raise HTTPException(404, f"Posición con ID {id_posacion} no encontrada")
    return posicion


@router.put("/{id_posicion}", response_model=PosicionFormacionResponse, summary="Actualizar posición de formación")
def actualizar_posicion_router(
    id_posicion: int,
    datos: PosicionFormacionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Actualiza los datos de una posición de formación.

    Parámetros:
        - id_posicion (int): ID de la posición a actualizar
        - datos (PosicionFormacionUpdate): Datos a actualizar (nombre, descripcion)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        PosicionFormacionResponse: Información de la posición actualizada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la posición no existe
        HTTPException 400: Si el nombre ya está en uso
    """
    try:
        return actualizar_posicion_formacion(db, id_posicion, datos)
    except ValueError as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.delete("/{id_posicion}", summary="Eliminar posición de formación")
def eliminar_posicion_router(
    id_posicion: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Elimina una posición de formación.

    Parámetros:
        - id_posicion (int): ID de la posición a eliminar
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la posición no existe
    """
    try:
        eliminar_posicion_formacion(db, id_posicion)
        return {"mensaje": f"Posición con ID {id_posicion} eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))