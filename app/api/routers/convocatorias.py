# app/api/routers/convocatorias.py
"""
Router de Convocatorias - Gestión de convocatorias de jugadores para partidos.
Endpoints para crear, obtener y eliminar convocatorias.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.schemas.convocatoria import ConvocatoriaCreate, ConvocatoriaPartidoResponse
from app.api.services.convocatoria_service import (
    crear_convocatoria,
    obtener_convocatoria_partido,
    obtener_convocatoria_equipo,
    eliminar_convocatoria
)

# Configuración del router
router = APIRouter(
    prefix="/convocatorias",
    tags=["Convocatorias"]
)


@router.post("/", summary="Crear convocatoria para un partido")
def crear_convocatoria_router(
    datos: ConvocatoriaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crea una convocatoria para un partido.

    Permite definir qué jugadores están convocados y cuáles son titulares.
    Si ya existe una convocatoria, la reemplaza.

    Parámetros:
        - datos (ConvocatoriaCreate): Datos de la convocatoria
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        List[ConvocatoriaPartido]: Lista de convocatorias creadas

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate

    Raises:
        HTTPException 400: Si hay más de 11 titulares
        HTTPException 404: Si el partido no existe
    """
    # Verificar permisos: admin, coach o delegate
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para crear convocatorias")

    try:
        return crear_convocatoria(db, datos)
    except ValueError as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get("/partido/{id_partido}", response_model=ConvocatoriaPartidoResponse, summary="Obtener convocatoria del partido")
def obtener_convocatoria_router(
    id_partido: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la convocatoria completa de un partido.

    Devuelve la lista de jugadores titulares y suplentes.

    Parámetros:
        - id_partido (int): ID del partido
        - db (Session): Sesión de base de datos

    Returns:
        ConvocatoriaPartidoResponse: Convocatoria con titulares y suplentes

    Requiere autenticación: No
    """
    try:
        convocatoria = obtener_convocatoria_partido(db, id_partido)
        if not convocatoria:
            return ConvocatoriaPartidoResponse(id_partido=id_partido, titulares=[], suplentes=[])
        return convocatoria
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/partido/{id_partido}/equipo/{id_equipo}", response_model=ConvocatoriaPartidoResponse, summary="Obtener convocatoria de un equipo")
def obtener_convocatoria_equipo_router(
    id_partido: int,
    id_equipo: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la convocatoria de un equipo específico para un partido.

    Útil para ver la convocatoria del equipo local y visitante por separado.

    Parámetros:
        - id_partido (int): ID del partido
        - id_equipo (int): ID del equipo
        - db (Session): Sesión de base de datos

    Returns:
        ConvocatoriaPartidoResponse: Convocatoria con titulares y suplentes del equipo

    Requiere autenticación: No
    """
    try:
        convocatoria = obtener_convocatoria_equipo(db, id_partido, id_equipo)
        if not convocatoria:
            return ConvocatoriaPartidoResponse(id_partido=id_partido, titulares=[], suplentes=[])
        return convocatoria
    except ValueError as e:
        if "no encontrado" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.delete("/partido/{id_partido}", summary="Eliminar convocatoria del partido")
def eliminar_convocatoria_router(
    id_partido: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Elimina la convocatoria de un partido.

    Parámetros:
        - id_partido (int): ID del partido
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin, Coach, Delegate
    """
    # Verificar permisos: admin, coach o delegate
    roles_permitidos = ["admin", "coach", "delegate"]
    if not any(rol.nombre in roles_permitidos for rol in current_user.roles):
        raise HTTPException(403, "No tienes permiso para eliminar convocatorias")

    try:
        eliminar_convocatoria(db, id_partido)
        return {"mensaje": "Convocatoria eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))