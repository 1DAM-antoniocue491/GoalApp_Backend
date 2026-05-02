# app/api/routers/notificaciones.py
"""
Router de Notificaciones - Gestión de notificaciones de usuario.
Endpoints para consultar, crear, marcar como leídas y eliminar notificaciones del usuario autenticado.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.schemas.notificacion import NotificacionResponse, NotificacionCreate
from app.api.services.notificacion_service import (
    obtener_notificaciones_usuario,
    obtener_no_leidas,
    crear_notificacion,
    marcar_notificacion_leida,
    marcar_todas_como_leidas,
    eliminar_notificacion
)

# Configuración del router
router = APIRouter(
    prefix="/notificaciones",  # Base path: /api/v1/notificaciones
    tags=["Notificaciones"]  # Agrupación en documentación
)


@router.get("/", response_model=list[NotificacionResponse])
def listar_notificaciones(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar notificaciones del usuario autenticado.

    Obtiene todas las notificaciones (leídas y no leídas) del usuario actual,
    ordenadas por fecha de creación descendente.

    Parámetros:
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        List[NotificacionResponse]: Lista de notificaciones del usuario

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    return obtener_notificaciones_usuario(db, current_user.id_usuario)


@router.get("/no-leidas", response_model=list[NotificacionResponse])
def listar_no_leidas(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar solo las notificaciones no leídas del usuario autenticado.

    Obtiene las notificaciones que aún no han sido marcadas como leídas,
    ordenadas por fecha de creación descendente.

    Parámetros:
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        List[NotificacionResponse]: Lista de notificaciones no leídas

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    return obtener_no_leidas(db, current_user.id_usuario)


@router.post("/", response_model=NotificacionResponse)
def crear_notificacion_router(
    datos: NotificacionCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear una nueva notificación para un usuario.

    Crea una notificación con tipo, título, mensaje y referencia opcional.
    Solo administradores pueden crear notificaciones manualmente.

    Parámetros:
        - datos (NotificacionCreate): Datos de la notificación
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        NotificacionResponse: Notificación creada

    Requiere autenticación: Sí
    Roles permitidos: Admin, Sistema
    """
    # Validar que solo admins puedan crear notificaciones manualmente
    if not any(rol.nombre == "admin" for rol in current_user.roles):
        raise HTTPException(status_code=403, detail="No tienes permiso para crear notificaciones")

    return crear_notificacion(db, datos)


@router.put("/mark-all-read")
def marcar_todas_leidas(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marcar todas las notificaciones del usuario como leídas.

    Cambia el estado de todas las notificaciones no leídas del usuario actual.

    Parámetros:
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación con número de notificaciones marcadas

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    cantidad = marcar_todas_como_leidas(db, current_user.id_usuario)
    return {"mensaje": f"{cantidad} notificaciones marcadas como leídas"}


@router.patch("/{notificacion_id}/leer")
def marcar_leida(
    notificacion_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marcar una notificación como leída.

    Cambia el estado de una notificación a leída. Solo el propietario de la
    notificación puede marcarla como leída.

    Parámetros:
        - notificacion_id (int): ID de la notificación (path parameter)
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Propietario de la notificación
    """
    try:
        marcar_notificacion_leida(db, notificacion_id, current_user.id_usuario)
        return {"mensaje": "Notificación marcada como leída"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{notificacion_id}")
def marcar_leida_put(
    notificacion_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marcar una notificación como leída (método PUT para compatibilidad).

    Cambia el estado de una notificación a leída. Solo el propietario de la
    notificación puede marcarla como leída.

    Parámetros:
        - notificacion_id (int): ID de la notificación (path parameter)
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Propietario de la notificación
    """
    try:
        marcar_notificacion_leida(db, notificacion_id, current_user.id_usuario)
        return {"mensaje": "Notificación marcada como leída", "leida": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{notificacion_id}")
def eliminar_notificacion_router(
    notificacion_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar una notificación.

    Elimina permanentemente una notificación. Solo el propietario puede eliminarla.

    Parámetros:
        - notificacion_id (int): ID de la notificación (path parameter)
        - current_user: Usuario autenticado obtenido del token JWT
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Propietario de la notificación
    """
    try:
        eliminar_notificacion(db, notificacion_id, current_user.id_usuario)
        return {"mensaje": "Notificación eliminada"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
