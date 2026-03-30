"""
Servicios de lógica de negocio para Rol.
Maneja operaciones CRUD de roles del sistema, incluyendo validación
de nombres únicos y gestión de permisos.
"""
from sqlalchemy.orm import Session

from app.models.rol import Rol
from app.schemas.rol import RolCreate, RolUpdate

# ============================================================
# CRUD ROLES
# ============================================================


def crear_rol(db: Session, datos: RolCreate):
    """
    Crea un nuevo rol en el sistema.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (RolCreate): Datos del rol (nombre y descripción)
    
    Returns:
        Rol: Objeto Rol creado con su ID asignado
    
    Raises:
        ValueError: Si ya existe un rol con ese nombre
    """
    # Verificar que el nombre del rol sea único
    existente = db.query(Rol).filter(Rol.nombre == datos.nombre).first()
    if existente:
        raise ValueError("Ya existe un rol con ese nombre")

    rol = Rol(
        nombre=datos.nombre,
        descripcion=datos.descripcion
    )

    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


def obtener_roles(db: Session):
    """
    Obtiene todos los roles registrados en el sistema.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
    
    Returns:
        list[Rol]: Lista con todos los roles
    """
    return db.query(Rol).all()


def obtener_rol_por_id(db: Session, rol_id: int):
    """
    Busca un rol por su ID.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        rol_id (int): ID del rol a buscar
    
    Returns:
        Rol: Objeto Rol si existe, None si no se encuentra
    """
    return db.query(Rol).filter(Rol.id_rol == rol_id).first()


def actualizar_rol(db: Session, rol_id: int, datos: RolUpdate):
    """
    Actualiza los datos de un rol existente.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        rol_id (int): ID del rol a actualizar
        datos (RolUpdate): Datos a actualizar (nombre y/o descripción)
    
    Returns:
        Rol: Objeto Rol actualizado
    
    Raises:
        ValueError: Si el rol no existe o el nuevo nombre ya está en uso
    """
    rol = obtener_rol_por_id(db, rol_id)
    if not rol:
        raise ValueError("Rol no encontrado")

    if datos.nombre is not None:
        # Verificar que el nuevo nombre sea único (excluyendo el rol actual)
        existente = db.query(Rol).filter(
            Rol.nombre == datos.nombre,
            Rol.id_rol != rol_id
        ).first()
        if existente:
            raise ValueError("Ya existe otro rol con ese nombre")

        rol.nombre = datos.nombre

    if datos.descripcion is not None:
        rol.descripcion = datos.descripcion

    db.commit()
    db.refresh(rol)
    return rol


def eliminar_rol(db: Session, rol_id: int):
    """
    Elimina un rol del sistema.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        rol_id (int): ID del rol a eliminar
    
    Raises:
        ValueError: Si el rol no existe
    """
    rol = obtener_rol_por_id(db, rol_id)
    if not rol:
        raise ValueError("Rol no encontrado")

    db.delete(rol)
    db.commit()

def asignar_rol_a_usuario(db: Session, usuario_id: int, rol_id: int):
    # tu lógica aquí
    pass