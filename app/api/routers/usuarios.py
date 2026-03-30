# app/api/routers/usuarios.py
"""
Router de Usuarios - Gestión de cuentas de usuario.
Endpoints para registro, listado, actualización y eliminación de usuarios.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role, get_current_user
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.schemas.seguimiento import SeguimientoResponse, LigaSeguidaResponse
from app.api.services.usuario_service import (
    crear_usuario,
    obtener_usuario_por_id,
    obtener_usuarios,
    actualizar_usuario,
    eliminar_usuario,
    seguir_liga,
    dejar_de_seguir_liga,
    obtener_ligas_seguidas
)

# Configuración del router
router = APIRouter(
    prefix="/usuarios",  # Base path: /api/v1/usuarios
    tags=["Usuarios"]  # Agrupación en documentación
)

@router.post("/", response_model=UsuarioResponse)
def registrar_usuario (
        usuario: UsuarioCreate,
        db: Session = Depends(get_db)
    ):
    """
    Registrar un nuevo usuario.
    
    Crea una nueva cuenta de usuario en el sistema. Este endpoint es público
    para permitir el auto-registro.
    
    Parámetros:
        - usuario (UsuarioCreate): Datos del usuario (nombre, email, contraseña)
        - db (Session): Sesión de base de datos
    
    Returns:
        UsuarioResponse: Información del usuario creado (sin contraseña)
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    try:
        usuario = crear_usuario(db, usuario)
        return usuario
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/", response_model=list[UsuarioResponse], dependencies=[Depends(require_role("admin"))])
def listar_usuarios(db: Session = Depends(get_db)):
    """
    Listar todos los usuarios.
    
    Obtiene la lista completa de usuarios registrados en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[UsuarioResponse]: Lista de todos los usuarios
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return obtener_usuarios(db)

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """
    Obtener un usuario por su ID.
    
    Devuelve la información detallada de un usuario específico.
    
    Parámetros:
        - usuario_id (int): ID único del usuario (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        UsuarioResponse: Información completa del usuario
    
    Requiere autenticación: No
    Roles permitidos: Público
    
    Raises:
        HTTPException 404: Si el usuario no existe
    """
    usuario = obtener_usuario_por_id(db, usuario_id)
    # Validar que el usuario exista
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    return usuario

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario_router(usuario_id: int, datos: UsuarioUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de un usuario.
    
    Modifica los datos de un usuario existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - usuario_id (int): ID del usuario a actualizar (path parameter)
        - datos (UsuarioUpdate): Campos del usuario a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        UsuarioResponse: Información actualizada del usuario
    
    Requiere autenticación: Sí (idealmente validar que el usuario solo modifique su propia cuenta)
    Roles permitidos: Usuario propietario o Admin
    """
    return actualizar_usuario(db, usuario_id, datos)

@router.delete("/{usuario_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_usuario_router(usuario_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un usuario.
    
    Elimina un usuario del sistema. Esta acción puede afectar registros relacionados
    como notificaciones y asignaciones de roles.
    
    Parámetros:
        - usuario_id (int): ID del usuario a eliminar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_usuario(db, usuario_id)
    return {"mensaje": "Usuario eliminado correctamente"}

# ============================================================
# SEGUIMIENTO DE LIGAS
# ============================================================

@router.post("/me/ligas/{liga_id}/seguir", response_model=SeguimientoResponse)
def seguir_liga_router(
    liga_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Seguir una liga.

    Permite al usuario autenticado seguir una liga para recibir
    notificaciones sobre eventos relevantes de la misma.

    Parámetros:
        - liga_id (int): ID de la liga a seguir (path parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        SeguimientoResponse: Información del seguimiento creado

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados

    Raises:
        HTTPException 400: Si ya sigue la liga
        HTTPException 404: Si la liga no existe
    """
    try:
        return seguir_liga(db, current_user.id_usuario, liga_id)
    except ValueError as e:
        if "no encontrada" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))

@router.delete("/me/ligas/{liga_id}/seguir")
def dejar_de_seguir_liga_router(
    liga_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Dejar de seguir una liga.

    Elimina la relación de seguimiento entre el usuario autenticado y la liga.

    Parámetros:
        - liga_id (int): ID de la liga a dejar de seguir (path parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados

    Raises:
        HTTPException 400: Si no sigue la liga
    """
    try:
        dejar_de_seguir_liga(db, current_user.id_usuario, liga_id)
        return {"mensaje": "Has dejado de seguir la liga"}
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/me/ligas-seguidas", response_model=list[LigaSeguidaResponse])
def obtener_ligas_seguidas_router(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener las ligas que sigue el usuario autenticado.

    Devuelve la lista de ligas que el usuario está siguiendo.

    Parámetros:
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        List[LigaSeguidaResponse]: Lista de ligas seguidas

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    return obtener_ligas_seguidas(db, current_user.id_usuario)
