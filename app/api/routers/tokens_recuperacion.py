# app/api/routers/tokens_recuperacion.py
"""
Router de Tokens de Recuperación - Gestión administrativa de tokens.
Endpoints para consultar, invalidar y limpiar tokens de recuperación de contraseña.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, require_role
from app.schemas.token_recuperacion import (
    TokenRecuperacionResponse,
    TokenDetalladoResponse,
    TokenEstadisticasResponse
)
from app.api.services.token_recuperacion_service import (
    obtener_tokens_usuario,
    obtener_token_por_id,
    obtener_tokens_activos,
    obtener_tokens_expirados,
    invalidar_token,
    invalidar_tokens_usuario,
    limpiar_tokens_expirados,
    eliminar_token,
    obtener_estadisticas_tokens
)

# Configuración del router
router = APIRouter(
    prefix="/tokens-recuperacion",
    tags=["Tokens de Recuperación"]
)


@router.get("/estadisticas", response_model=TokenEstadisticasResponse, summary="Obtener estadísticas de tokens")
def obtener_estadisticas_router(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Obtiene estadísticas generales de los tokens de recuperación.

    Devuelve el total de tokens, activos, usados y expirados.

    Parámetros:
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        TokenEstadisticasResponse: Estadísticas de tokens

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return obtener_estadisticas_tokens(db)


@router.get("/activos", response_model=List[TokenRecuperacionResponse], summary="Listar tokens activos")
def listar_tokens_activos_router(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Obtiene todos los tokens de recuperación activos.

    Un token activo es aquel que no ha sido usado y no ha expirado.

    Parámetros:
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        List[TokenRecuperacionResponse]: Lista de tokens activos

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return obtener_tokens_activos(db)


@router.get("/expirados", response_model=List[TokenRecuperacionResponse], summary="Listar tokens expirados")
def listar_tokens_expirados_router(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Obtiene todos los tokens de recuperación expirados.

    Un token expirado es aquel cuya fecha de expiración ya pasó.

    Parámetros:
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        List[TokenRecuperacionResponse]: Lista de tokens expirados

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return obtener_tokens_expirados(db)


@router.get("/usuario/{id_usuario}", response_model=List[TokenRecuperacionResponse], summary="Obtener tokens de un usuario")
def obtener_tokens_usuario_router(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Obtiene todos los tokens de recuperación de un usuario específico.

    Parámetros:
        - id_usuario (int): ID del usuario
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        List[TokenRecuperacionResponse]: Lista de tokens del usuario

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    try:
        return obtener_tokens_usuario(db, id_usuario)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/{id_token}", response_model=TokenRecuperacionResponse, summary="Obtener token por ID")
def obtener_token_router(
    id_token: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Obtiene un token de recuperación por su ID.

    Parámetros:
        - id_token (int): ID del token
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        TokenRecuperacionResponse: Información del token

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si el token no existe
    """
    token = obtener_token_por_id(db, id_token)
    if not token:
        raise HTTPException(404, f"Token con ID {id_token} no encontrado")
    return token


@router.put("/{id_token}/invalidar", response_model=TokenRecuperacionResponse, summary="Invalidar un token")
def invalidar_token_router(
    id_token: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Invalida un token de recuperación específico.

    Marca el token como usado para que no pueda utilizarse.

    Parámetros:
        - id_token (int): ID del token a invalidar
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        TokenRecuperacionResponse: Token actualizado

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si el token no existe
    """
    try:
        return invalidar_token(db, id_token)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/usuario/{id_usuario}/invalidar", summary="Invalidar todos los tokens de un usuario")
def invalidar_tokens_usuario_router(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Invalida todos los tokens de recuperación activos de un usuario.

    Parámetros:
        - id_usuario (int): ID del usuario
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        dict: Mensaje con el número de tokens invalidados

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    try:
        cantidad = invalidar_tokens_usuario(db, id_usuario)
        return {"mensaje": f"Se invalidaron {cantidad} tokens del usuario {id_usuario}"}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/limpiar-expirados", summary="Eliminar tokens expirados")
def limpiar_tokens_expirados_router(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Elimina todos los tokens de recuperación expirados de la base de datos.

    Esta operación es útil para mantenimiento y limpieza periódica.

    Parámetros:
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        dict: Mensaje con el número de tokens eliminados

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    cantidad = limpiar_tokens_expirados(db)
    return {"mensaje": f"Se eliminaron {cantidad} tokens expirados"}


@router.delete("/{id_token}", summary="Eliminar un token")
def eliminar_token_router(
    id_token: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Elimina un token de recuperación específico.

    Parámetros:
        - id_token (int): ID del token a eliminar
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere rol admin)

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si el token no existe
    """
    try:
        eliminar_token(db, id_token)
        return {"mensaje": f"Token con ID {id_token} eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))