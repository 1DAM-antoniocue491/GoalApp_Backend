# app/api/services/token_recuperacion_service.py
"""
Servicios de lógica de negocio para TokenRecuperacion.
Maneja operaciones de gestión de tokens de recuperación de contraseña.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.token_recuperacion import TokenRecuperacion
from app.models.usuario import Usuario


def obtener_tokens_usuario(db: Session, id_usuario: int) -> List[TokenRecuperacion]:
    """
    Obtiene todos los tokens de recuperación de un usuario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_usuario (int): ID del usuario

    Returns:
        List[TokenRecuperacion]: Lista de tokens del usuario

    Raises:
        ValueError: Si el usuario no existe
    """
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise ValueError(f"Usuario con ID {id_usuario} no encontrado")

    return db.query(TokenRecuperacion).filter(
        TokenRecuperacion.id_usuario == id_usuario
    ).order_by(TokenRecuperacion.created_at.desc()).all()


def obtener_token_por_id(db: Session, id_token: int) -> Optional[TokenRecuperacion]:
    """
    Obtiene un token de recuperación por su ID.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_token (int): ID del token

    Returns:
        TokenRecuperacion | None: El token si existe, None si no
    """
    return db.query(TokenRecuperacion).filter(
        TokenRecuperacion.id_token == id_token
    ).first()


def obtener_tokens_activos(db: Session) -> List[TokenRecuperacion]:
    """
    Obtiene todos los tokens de recuperación activos (no usados y no expirados).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        List[TokenRecuperacion]: Lista de tokens activos
    """
    ahora = datetime.utcnow()
    return db.query(TokenRecuperacion).filter(
        TokenRecuperacion.usado == False,
        TokenRecuperacion.fecha_expiracion > ahora
    ).order_by(TokenRecuperacion.created_at.desc()).all()


def obtener_tokens_expirados(db: Session) -> List[TokenRecuperacion]:
    """
    Obtiene todos los tokens de recuperación expirados.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        List[TokenRecuperacion]: Lista de tokens expirados
    """
    ahora = datetime.utcnow()
    return db.query(TokenRecuperacion).filter(
        TokenRecuperacion.fecha_expiracion <= ahora
    ).order_by(TokenRecuperacion.created_at.desc()).all()


def invalidar_token(db: Session, id_token: int) -> TokenRecuperacion:
    """
    Marca un token como usado/invalidado.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_token (int): ID del token a invalidar

    Returns:
        TokenRecuperacion: Token actualizado

    Raises:
        ValueError: Si el token no existe
    """
    token = obtener_token_por_id(db, id_token)
    if not token:
        raise ValueError(f"Token con ID {id_token} no encontrado")

    token.usado = True
    db.commit()
    db.refresh(token)
    return token


def invalidar_tokens_usuario(db: Session, id_usuario: int) -> int:
    """
    Invalida todos los tokens de recuperación de un usuario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_usuario (int): ID del usuario

    Returns:
        int: Número de tokens invalidados

    Raises:
        ValueError: Si el usuario no existe
    """
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise ValueError(f"Usuario con ID {id_usuario} no encontrado")

    # Contar tokens activos antes de invalidar
    tokens_activos = db.query(TokenRecuperacion).filter(
        TokenRecuperacion.id_usuario == id_usuario,
        TokenRecuperacion.usado == False
    ).all()

    # Invalidar todos
    for token in tokens_activos:
        token.usado = True

    db.commit()
    return len(tokens_activos)


def limpiar_tokens_expirados(db: Session) -> int:
    """
    Elimina todos los tokens expirados de la base de datos.

    Esta función es útil para mantenimiento y limpieza periódica.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        int: Número de tokens eliminados
    """
    ahora = datetime.utcnow()
    resultado = db.query(TokenRecuperacion).filter(
        TokenRecuperacion.fecha_expiracion <= ahora
    ).delete()
    db.commit()
    return resultado


def eliminar_token(db: Session, id_token: int) -> bool:
    """
    Elimina un token de recuperación de la base de datos.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        id_token (int): ID del token a eliminar

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si el token no existe
    """
    token = obtener_token_por_id(db, id_token)
    if not token:
        raise ValueError(f"Token con ID {id_token} no encontrado")

    db.delete(token)
    db.commit()
    return True


def obtener_estadisticas_tokens(db: Session) -> dict:
    """
    Obtiene estadísticas generales de los tokens de recuperación.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy

    Returns:
        dict: Estadísticas de tokens (total, activos, usados, expirados)
    """
    ahora = datetime.utcnow()

    total = db.query(TokenRecuperacion).count()
    usados = db.query(TokenRecuperacion).filter(TokenRecuperacion.usado == True).count()
    activos = db.query(TokenRecuperacion).filter(
        TokenRecuperacion.usado == False,
        TokenRecuperacion.fecha_expiracion > ahora
    ).count()
    expirados = db.query(TokenRecuperacion).filter(
        TokenRecuperacion.usado == False,
        TokenRecuperacion.fecha_expiracion <= ahora
    ).count()

    return {
        "total": total,
        "activos": activos,
        "usados": usados,
        "expirados": expirados
    }