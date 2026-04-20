# app/api/routers/auth.py
"""
Router de Autenticación - Gestión de autenticación y autorización.
Endpoints para login, obtención de usuario actual y renovación de tokens JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.api.dependencies import (
    get_db,
    get_current_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)

from app.api.services.usuario_service import (
    autenticar_usuario,
    obtener_usuario_por_email,
    crear_token_recuperacion,
    validar_token_recuperacion,
    marcar_token_usado,
    cambiar_contrasena_usuario
)
from app.api.services.email_service import enviar_email_recuperacion
from app.schemas.usuario import UsuarioResponse
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse

# Configuración del router
router = APIRouter(
    prefix="/auth",  # Base path: /api/v1/auth
    tags=["Autenticación"]  # Agrupación en documentación
)

# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario y generar tokens de acceso y refresh.

    Valida las credenciales del usuario (email y contraseña) y genera tokens JWT
    para acceder a los endpoints protegidos de la API.

    Parámetros:
        - form_data (OAuth2PasswordRequestForm): Formulario con username (email) y password
        - db (Session): Sesión de base de datos

    Returns:
        dict: Tokens de acceso y refresh JWT
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "expires_in": 2592000
        }

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 401: Si las credenciales son incorrectas
    """
    # Autenticar usuario mediante servicio
    usuario = autenticar_usuario(db, form_data.username, form_data.password)

    # Validar que el usuario exista y la contraseña sea correcta
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # Configurar tiempo de expiración del access token (30 días)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Crear access token JWT con el ID del usuario
    access_token = create_access_token(
        data={"sub": str(usuario.id_usuario)},
        expires_delta=access_token_expires
    )

    # Crear refresh token con expiración de 90 días (más largo)
    refresh_token_expires = timedelta(days=90)
    refresh_token = create_access_token(
        data={"sub": str(usuario.id_usuario), "type": "refresh"},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": int(access_token_expires.total_seconds())
    }

# ============================================================
# USUARIO ACTUAL
# ============================================================

@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(current_user = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado.
    
    Devuelve los datos completos del usuario que está actualmente autenticado
    mediante el token JWT proporcionado en el header Authorization.
    
    Parámetros:
        - current_user: Usuario autenticado obtenido del token JWT
    
    Returns:
        UsuarioResponse: Información completa del usuario autenticado
    
    Requiere autenticación: Sí
    Roles permitidos: Todos los usuarios autenticados
    """
    return current_user

# ============================================================
# REFRESH TOKEN
# ============================================================

@router.post("/refresh")
def refresh_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Renovar token de acceso usando un refresh token.
    
    Valida un refresh token y genera un nuevo access token si el refresh token
    es válido y el usuario aún existe en el sistema.
    
    Parámetros:
        - token (str): Refresh token JWT válido
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Nuevo token de acceso JWT
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer"
        }
    
    Requiere autenticación: No (pero requiere refresh token válido)
    Roles permitidos: Público
    
    Raises:
        HTTPException 401: Si el refresh token es inválido o el usuario no existe
    """
    from jose import jwt, JWTError

    try:
        # Decodificar el refresh token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        # Validar que el token contenga el ID de usuario
        if user_id is None:
            raise HTTPException(401, "Refresh token inválido")

    except JWTError:
        raise HTTPException(401, "Refresh token inválido")

    # Buscar usuario en la base de datos
    from app.api.services.usuario_service import obtener_usuario_por_id
    usuario = obtener_usuario_por_id(db, user_id)

    # Validar que el usuario exista
    if not usuario:
        raise HTTPException(401, "Refresh token inválido")

    # Crear nuevo access token
    nuevo_access_token = create_access_token({"sub": str(usuario.id_usuario)})

    return {
        "access_token": nuevo_access_token,
        "token_type": "bearer"
    }

# ============================================================
# RECUPERACIÓN DE CONTRASEÑA
# ============================================================

@router.post("/forgot-password", response_model=PasswordResetResponse)
def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Solicitar recuperación de contraseña.

    Genera un token de recuperación y envía un email al usuario con
    el enlace para restablecer su contraseña.

    Parámetros:
        - request (PasswordResetRequest): Email del usuario
        - background_tasks (BackgroundTasks): Tareas en segundo plano de FastAPI
        - db (Session): Sesión de base de datos

    Returns:
        PasswordResetResponse: Mensaje de confirmación

    Requiere autenticación: No
    Roles permitidos: Público

    Nota:
        Por seguridad, siempre devuelve éxito incluso si el email no existe.
    """
    # Buscar usuario por email
    usuario = obtener_usuario_por_email(db, request.email)

    if usuario:
        # Generar token de recuperación
        token = crear_token_recuperacion(db, usuario.id_usuario)

        # Enviar email en segundo plano
        background_tasks.add_task(
            enviar_email_recuperacion,
            email_destino=usuario.email,
            token=token,
            nombre_usuario=usuario.nombre
        )

    # Por seguridad, siempre devolver éxito
    return PasswordResetResponse(
        mensaje="Si el email está registrado, recibirás instrucciones para recuperar tu contraseña"
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Restablecer contraseña usando token de recuperación.

    Valida el token de recuperación y actualiza la contraseña del usuario.

    Parámetros:
        - request (PasswordResetConfirm): Token y nueva contraseña

    Returns:
        PasswordResetResponse: Mensaje de confirmación

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 400: Si el token es inválido o ha expirado
    """
    # Validar token
    usuario = validar_token_recuperacion(db, request.token)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )

    # Cambiar contraseña
    cambiar_contrasena_usuario(db, usuario.id_usuario, request.nueva_contrasena)

    # Marcar token como usado
    marcar_token_usado(db, request.token)

    return PasswordResetResponse(
        mensaje="Contraseña actualizada correctamente"
    )
