# app/api/routers/usuarios.py
"""
Router de Usuarios - Gestión de cuentas de usuario.
Endpoints para registro, listado, actualización y eliminación de usuarios.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role, get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, LigaConRolResponse, UsuarioConRolEnLigaResponse
from app.schemas.seguimiento import SeguimientoResponse, LigaSeguidaResponse
from app.schemas.gestion_usuarios import UsuarioRolUpdate, UsuarioEstadoUpdate, UsuarioLigaResponse
from app.api.services.usuario_service import (
    crear_usuario,
    obtener_usuario_por_id,
    obtener_usuarios,
    actualizar_usuario,
    eliminar_usuario,
    seguir_liga,
    dejar_de_seguir_liga,
    obtener_ligas_seguidas,
    obtener_ligas_con_rol,
    obtener_usuarios_con_rol_en_liga,
    relevo_admin,
    cambiar_rol_en_liga,
    eliminar_asignacion_liga,
    cambiar_estado_usuario_en_liga,
    obtener_usuarios_con_roles
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

@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(current_user: Usuario = Depends(get_current_user)):
    """
    Obtener el usuario autenticado actualmente.

    Devuelve la información del usuario asociado al token JWT.

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    return current_user

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Obtener un usuario por su ID.

    Devuelve la información detallada de un usuario específico.

    Parámetros:
        - usuario_id (int): ID único del usuario (path parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (requiere auth)

    Returns:
        UsuarioResponse: Información completa del usuario

    Requiere autenticación: Sí
    Roles permitidos: Usuarios autenticados

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 401: Si no está autenticado
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


@router.get("/me/ligas", response_model=list[LigaConRolResponse])
def obtener_ligas_usuario_router(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener las ligas donde el usuario tiene un rol asignado.

    Devuelve la lista de ligas donde el usuario autenticado tiene algun rol
    (admin, entrenador, jugador, delegado, observador).

    Parámetros:
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        List[LigaConRolResponse]: Lista de ligas con el rol del usuario en cada una

    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    return obtener_ligas_con_rol(db, current_user.id_usuario)


@router.get("/ligas/{liga_id}/usuarios", response_model=list[UsuarioConRolEnLigaResponse])
def obtener_usuarios_con_rol(
    liga_id: int,
    solo_activos: bool = False,
    db: Session = Depends(get_db)
):
    """
    Obtener todos los usuarios con roles asignados en una liga específica.

    Devuelve la lista de usuarios que tienen algún rol (admin, entrenador, delegado, jugador, etc.)
    en la liga especificada. Útil para mostrar estadísticas de usuarios por liga.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - solo_activos (bool): Si True, filtra solo usuarios activos
        - db (Session): Sesión de base de datos

    Returns:
        List[UsuarioConRolEnLigaResponse]: Lista de usuarios con su rol en la liga

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_usuarios_con_rol_en_liga(db, liga_id, solo_activos=solo_activos)


@router.get("/ligas/{liga_id}/stats")
def obtener_stats_usuarios(
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de usuarios en una liga.

    Retorna:
        - total: Total de usuarios con rol en la liga
        - activos: Usuarios con activo=1
        - pendientes: Usuarios con activo=0
        - admin_activos: Admins con activo=1

    Requiere autenticación: No
    Roles permitidos: Público
    """
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol

    # Obtener todos los usuarios con rol en esta liga
    usuarios = db.query(UsuarioRol).filter(UsuarioRol.id_liga == liga_id).all()

    total = len(usuarios)
    activos = sum(1 for u in usuarios if u.activo)
    pendientes = total - activos

    # Obtener IDs de rol de admin (nombre = "admin")
    admin_rol = db.query(Rol).filter(Rol.nombre == "admin").first()
    admin_activos = sum(1 for u in usuarios if u.activo and u.id_rol == admin_rol.id_rol) if admin_rol else 0

    return {
        "total": total,
        "activos": activos,
        "pendientes": pendientes,
        "admin_activos": admin_activos
    }


# ============================================================
# GESTIÓN DE USUARIOS DE LIGA (ADMIN)
# ============================================================

@router.put("/{usuario_id}/rol", response_model=UsuarioLigaResponse, dependencies=[Depends(require_role("admin"))])
def cambiar_rol_usuario(
    usuario_id: int,
    datos: UsuarioRolUpdate,
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Cambiar el rol de un usuario en una liga específica.

    Permite a un administrador modificar el rol asignado a un usuario dentro de una liga.
    Útil para promover/degradar usuarios entre diferentes niveles de permiso.

    Parámetros:
        - usuario_id (int): ID del usuario (path parameter)
        - liga_id (int): ID de la liga (query parameter)
        - datos (UsuarioRolUpdate): {"id_rol": int} con el nuevo rol a asignar

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario con su nuevo rol

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 400: Si el usuario no tiene rol asignado o el rol no existe
        HTTPException 404: Si la liga no existe
    """
    try:
        asignacion = cambiar_rol_en_liga(db, usuario_id, liga_id, datos.id_rol)
        return UsuarioLigaResponse(
            id_usuario_rol=asignacion.id_usuario_rol,
            id_usuario=asignacion.id_usuario,
            nombre_usuario=asignacion.usuario.nombre,
            email=asignacion.usuario.email,
            id_rol=asignacion.id_rol,
            nombre_rol=asignacion.rol.nombre,
            activo=asignacion.activo
        )
    except ValueError as e:
        if "no encontrada" in str(e) or "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{usuario_id}/liga", dependencies=[Depends(require_role("admin"))])
def eliminar_usuario_de_liga(
    usuario_id: int,
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar la asignación de un usuario en una liga específica.

    Remueve completamente la relación entre el usuario y la liga, eliminando
    cualquier rol que tuviera asignado.

    Parámetros:
        - usuario_id (int): ID del usuario (path parameter)
        - liga_id (int): ID de la liga (query parameter)

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 400: Si el usuario no tiene un rol asignado en esa liga
    """
    try:
        eliminar_asignacion_liga(db, usuario_id, liga_id)
        return {"mensaje": "Usuario eliminado de la liga correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{usuario_id}/estado", response_model=UsuarioLigaResponse, dependencies=[Depends(require_role("admin"))])
def cambiar_estado_usuario(
    usuario_id: int,
    datos: UsuarioEstadoUpdate,
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Activar o desactivar un usuario en una liga específica.

    Permite a un administrador cambiar el estado de un usuario entre activo e inactivo.
    Los usuarios inactivos no pueden realizar acciones en la liga pero mantienen su rol.

    Parámetros:
        - usuario_id (int): ID del usuario (path parameter)
        - liga_id (int): ID de la liga (query parameter)
        - datos (UsuarioEstadoUpdate): {"activo": bool}

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario con su nuevo estado

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 400: Si el usuario no tiene un rol asignado en esa liga
    """
    try:
        return cambiar_estado_usuario_en_liga(db, usuario_id, liga_id, datos.activo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ligas/{liga_id}/roles", response_model=list[UsuarioLigaResponse], dependencies=[Depends(require_role("admin"))])
def listar_usuarios_con_roles(
    liga_id: int,
    db: Session = Depends(get_db)
):
    """
    Listar todos los usuarios con sus roles asignados en una liga específica.

    Devuelve información completa de cada usuario incluyendo su rol actual
    y estado de activación dentro de la liga.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[UsuarioLigaResponse]: Lista de usuarios con sus roles en la liga

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga no existe
    """
    try:
        usuarios = obtener_usuarios_con_roles(db, liga_id)
        return [
            UsuarioLigaResponse(
                id_usuario_rol=u["id_usuario_rol"],
                id_usuario=u["id_usuario"],
                nombre_usuario=u["nombre_usuario"],
                email=u["email"],
                id_rol=u["id_rol"],
                nombre_rol=u["nombre_rol"],
                activo=u["activo"]
            )
            for u in usuarios
        ]
    except ValueError as e:
        if "no encontrada" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# RELEVO DE ADMINISTRADOR
# ============================================================


@router.post("/ligas/{liga_id}/relevo-admin", dependencies=[Depends(require_role("admin"))])
def relevo_admin_endpoint(
    liga_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Realiza el relevo de administrador de una liga.
    El admin actual pasa a ser viewer y el nuevo usuario se convierte en admin.

    Args:
        liga_id: ID de la liga
        payload: {"nuevo_admin_id": int}
        current_user: Admin actual que realiza el relevo

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException 400: Si faltan datos o hay error de validación
        HTTPException 401: Si no está autenticado
        HTTPException 403: Si no tiene rol de admin
    """
    nuevo_admin_id = payload.get("nuevo_admin_id")
    if not nuevo_admin_id:
        raise HTTPException(status_code=400, detail="nuevo_admin_id es requerido")

    try:
        relevo_admin(db, liga_id, current_user.id_usuario, nuevo_admin_id)
        return {"message": "Relevo de administrador completado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
