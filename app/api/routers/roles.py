# app/api/routers/roles.py
"""
Router de Roles - Gestión de roles y permisos de usuario.
Endpoints para crear, listar, actualizar, eliminar roles y asignarlos a usuarios.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.rol import RolCreate, RolUpdate, RolResponse
from app.api.services.rol_service import (
    crear_rol,
    obtener_roles,
    actualizar_rol,
    eliminar_rol,
    asignar_rol_a_usuario
)

# Configuración del router
router = APIRouter(
    prefix="/roles",  # Base path: /api/v1/roles
    tags=["Roles"]  # Agrupación en documentación
)

@router.post("/", response_model=RolResponse, dependencies=[Depends(require_role("admin"))])
def crear_rol_router(rol: RolCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo rol.
    
    Registra un nuevo rol en el sistema con sus permisos asociados.
    
    Parámetros:
        - rol (RolCreate): Datos del rol (nombre, descripción, permisos)
        - db (Session): Sesión de base de datos
    
    Returns:
        RolResponse: Información del rol creado con su ID asignado
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_rol(db, rol)

@router.get("/", response_model=list[RolResponse])
def listar_roles(db: Session = Depends(get_db)):
    """
    Listar todos los roles.
    
    Obtiene la lista completa de roles registrados en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[RolResponse]: Lista de todos los roles
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_roles(db)

@router.put("/{rol_id}", response_model=RolResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_rol_router(rol_id: int, datos: RolUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de un rol.
    
    Modifica los datos de un rol existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - rol_id (int): ID del rol a actualizar (path parameter)
        - datos (RolUpdate): Campos del rol a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        RolResponse: Información actualizada del rol
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_rol(db, rol_id, datos)

@router.delete("/{rol_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_rol_router(rol_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un rol.
    
    Elimina un rol del sistema. Esta acción puede afectar a los usuarios
    que tienen este rol asignado.
    
    Parámetros:
        - rol_id (int): ID del rol a eliminar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_rol(db, rol_id)
    return {"mensaje": "Rol eliminado"}

@router.post("/asignar/{usuario_id}/{rol_id}", dependencies=[Depends(require_role("admin"))])
def asignar_rol(usuario_id: int, rol_id: int, db: Session = Depends(get_db)):
    """
    Asignar un rol a un usuario.
    
    Vincula un rol existente a un usuario específico, otorgándole los permisos
    asociados a ese rol.
    
    Parámetros:
        - usuario_id (int): ID del usuario (path parameter)
        - rol_id (int): ID del rol a asignar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    # Asignar el rol al usuario mediante el servicio
    asignar_rol_a_usuario(db, usuario_id, rol_id)
    return {"mensaje": "Rol asignado correctamente"}
