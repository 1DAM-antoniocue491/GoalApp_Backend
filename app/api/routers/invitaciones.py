# app/api/routers/invitaciones.py
"""
Router de Invitaciones - Gestión de invitaciones a ligas.
Endpoints para enviar invitaciones por email y aceptarlas.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.dependencies import get_db, get_current_user, require_role
from app.schemas.invitacion import InvitacionCreate, InvitacionValidarResponse, InvitacionAceptar
from app.api.services.invitacion_service import (
    crear_invitacion,
    validar_token_invitacion,
    aceptar_invitacion,
    aceptar_invitacion_usuario_existente,
    verificar_usuario_existente
)

# Configuración del router
router = APIRouter(
    prefix="/invitaciones",
    tags=["Invitaciones"]
)

# ============================================================
# CREAR INVITACIÓN (solo admin de la liga)
# ============================================================

@router.post("/ligas/{liga_id}/invitar", status_code=status.HTTP_201_CREATED)
def invitar_a_liga(
    liga_id: int,
    datos: InvitacionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Enviar invitación a un usuario para unirse a una liga.

    Si el usuario ya existe (por email), se le asigna el rol directamente.
    Si no existe, se crea una invitación con token y se envía email con enlace de registro.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - datos (InvitacionCreate): Email, rol, equipo, dorsal, posición, tipo de jugador
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (debe ser admin de la liga)

    Returns:
        dict: Mensaje indicando si se creó invitación o se asignó rol directamente

    Requiere autenticación: Sí
    Roles permitidos: Admin de la liga
    """
    # Verificar que el usuario actual es admin de la liga
    try:
        from app.api.services.liga_service import verificar_admin_liga
        verificar_admin_liga(db, liga_id, current_user.id_usuario)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador en esta liga"
        )

    # Verificar si el usuario ya existe por email
    usuario_existente = verificar_usuario_existente(db, datos.email)

    if usuario_existente:
        # El usuario ya existe, asignar rol directamente
        from app.api.services.invitacion_service import asignar_rol_directamente
        asignar_rol_directamente(
            db=db,
            id_usuario=usuario_existente.id_usuario,
            id_liga=liga_id,
            id_rol=datos.id_rol,
            id_equipo=datos.id_equipo,
            dorsal=datos.dorsal,
            posicion=datos.posicion,
            tipo_jugador=datos.tipo_jugador
        )
        return {
            "mensaje": f"El usuario {datos.email} ya estaba registrado. Se le ha asignado el rol directamente.",
            "usuario_id": usuario_existente.id_usuario,
            "rol_asignado": True
        }

    # El usuario no existe, crear invitación
    invitacion = crear_invitacion(
        db=db,
        email=datos.email,
        id_liga=liga_id,
        id_rol=datos.id_rol,
        id_equipo=datos.id_equipo,
        dorsal=datos.dorsal,
        posicion=datos.posicion,
        tipo_jugador=datos.tipo_jugador,
        invitado_por=current_user.id_usuario
    )

    # Enviar email de invitación (en background)
    # TODO: Implementar envío de email cuando esté configurado el SMTP

    return {
        "mensaje": "Invitación creada. Se ha enviado un email al usuario.",
        "token": invitacion.token,
        "email": datos.email
    }


# ============================================================
# VALIDAR TOKEN DE INVITACIÓN
# ============================================================

@router.get("/validar/{token}", response_model=InvitacionValidarResponse)
def validar_invitacion(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Validar un token de invitación.

    Verifica si el token existe, no está usado y no ha expirado.

    Parámetros:
        - token (str): Token de invitación a validar
        - db (Session): Sesión de base de datos

    Returns:
        InvitacionValidarResponse:
            - valido (bool): True si el token es válido
            - email (str): Email del invitado (si es válido)
            - liga_nombre (str): Nombre de la liga (si es válido)
            - equipo_nombre (str): Nombre del equipo (si es válido)
            - rol (str): Nombre del rol (si es válido)
            - motivo (str): Motivo por el que no es válido (si no lo es)

    Requiere autenticación: No
    """
    resultado = validar_token_invitacion(db, token)

    if not resultado["valido"]:
        return InvitacionValidarResponse(
            valido=False,
            motivo=resultado.get("motivo", "Token inválido")
        )

    return InvitacionValidarResponse(
        valido=True,
        email=resultado["email"],
        liga_nombre=resultado["liga_nombre"],
        equipo_nombre=resultado.get("equipo_nombre"),
        rol=resultado["rol"],
        dorsal=resultado.get("dorsal"),
        posicion=resultado.get("posicion"),
        tipo_jugador=resultado.get("tipo_jugador")
    )


# ============================================================
# ACEPTAR INVITACIÓN (registro)
# ============================================================

@router.post("/aceptar/{token}")
def aceptar_invitacion_endpoint(
    token: str,
    datos: InvitacionAceptar,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Aceptar una invitación y crear usuario.

    Valida el token y crea el usuario con el rol asignado.

    Parámetros:
        - token (str): Token de invitación
        - datos (InvitacionAceptar): Email, contraseña, nombre
        - db ( Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación y datos del usuario creado

    Requiere autenticación: No
    """
    # Validar que el email coincide
    invitacion = validar_token_invitacion(db, token)

    if not invitacion["valido"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitación inválida o expirada: {invitacion.get('motivo', 'desconocido')}"
        )

    # Verificar que el email coincide
    if datos.email.lower() != invitacion["email"].lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email no coincide con la invitación"
        )

    # Crear usuario y asignar rol
    try:
        usuario = aceptar_invitacion(
            db=db,
            token=token,
            email=datos.email,
            password=datos.password,
            nombre=datos.nombre
        )

        return {
            "mensaje": "Invitación aceptada correctamente. Usuario creado.",
            "usuario_id": usuario.id_usuario,
            "email": usuario.email
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/aceptar-existente/{token}")
def aceptar_invitacion_existente_endpoint(
    token: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Aceptar una invitación cuando el usuario ya tiene cuenta.

    Valida el token y activa el rol del usuario en la liga.

    Parámetros:
        - token (str): Token de invitación
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    """
    try:
        aceptar_invitacion_usuario_existente(
            db=db,
            token=token,
            usuario_id=current_user.id_usuario
        )

        return {
            "mensaje": "Invitación aceptada correctamente. Rol activado.",
            "usuario_id": current_user.id_usuario
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================
# ACTIVAR USUARIO (solo admin de la liga)
# ============================================================

@router.post("/ligas/{liga_id}/usuarios/{usuario_id}/activar")
def activar_usuario_liga(
    liga_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Activar manualmente un usuario en una liga.

    Permite a un admin activar un usuario que está pendiente.

    Parámetros:
        - liga_id (int): ID de la liga
        - usuario_id (int): ID del usuario a activar
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (debe ser admin)

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin de la liga
    """
    # Verificar que el usuario actual es admin de la liga
    try:
        from app.api.services.liga_service import verificar_admin_liga
        verificar_admin_liga(db, liga_id, current_user.id_usuario)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador en esta liga"
        )

    # Buscar la asignación usuario-rol-liga
    usuario_rol = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not usuario_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en esta liga"
        )

    # Activar usuario
    usuario_rol.activo = 1
    db.commit()

    return {
        "mensaje": "Usuario activado correctamente",
        "usuario_id": usuario_id,
        "liga_id": liga_id
    }
