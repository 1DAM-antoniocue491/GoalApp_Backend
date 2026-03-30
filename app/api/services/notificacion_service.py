"""
Servicios de lógica de negocio para Notificación.
Maneja la gestión de notificaciones para usuarios, permitiendo consultar
y marcar notificaciones como leídas.
"""
from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion


def obtener_notificaciones_usuario(db: Session, usuario_id: int):
    """
    Obtiene todas las notificaciones de un usuario específico.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
    
    Returns:
        list[Notificacion]: Lista de notificaciones del usuario
    """
    return db.query(Notificacion).filter(Notificacion.id_usuario == usuario_id).all()


def marcar_notificacion_leida(db: Session, notificacion_id: int, usuario_id: int):
    """
    Marca una notificación como leída.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        notificacion_id (int): ID de la notificación a marcar
        usuario_id (int): ID del usuario propietario (validación de pertenencia)
    
    Returns:
        bool: True si se marcó correctamente
    
    Raises:
        ValueError: Si la notificación no existe o no pertenece al usuario
    """
    # Buscar la notificación y verificar que pertenece al usuario
    notificacion = db.query(Notificacion).filter(
        Notificacion.id_notificacion == notificacion_id,
        Notificacion.id_usuario == usuario_id
    ).first()

    if not notificacion:
        raise ValueError("Notificación no encontrada")

    # Marcar como leída
    notificacion.leida = True
    db.commit()
    return True
