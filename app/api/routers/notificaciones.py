# app/api/routers/notificaciones.py
"""
Router de Notificaciones - Gestión de notificaciones de usuario.
Endpoints para consultar y marcar como leídas las notificaciones del usuario autenticado.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.schemas.notificacion import NotificacionResponse
from app.api.services.notificacion_service import (
    obtener_notificaciones_usuario,
    marcar_notificacion_leida
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

@router.put("/{notificacion_id}")
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
    # Marcar como leída validando que pertenece al usuario actual
    marcar_notificacion_leida(db, notificacion_id, current_user.id_usuario)
    return {"mensaje": "Notificación marcada como leída"}
