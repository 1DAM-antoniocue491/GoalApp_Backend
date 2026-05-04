# app/api/routers/invitaciones.py
"""
Router de Invitaciones - Gestión de invitaciones a ligas.
Endpoints para enviar invitaciones por email y aceptarlas.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.dependencies import get_db, get_current_user, require_role
from app.models.usuario import Usuario
from app.models.liga import Liga
from app.schemas.invitacion import (
    InvitacionCreate,
    InvitacionValidarResponse,
    InvitacionAceptar,
    InvitacionCodigoCreate,
    InvitacionCodigoResponse,
    InvitacionAceptarCodigo
)
from app.api.services.invitacion_service import (
    crear_invitacion,
    validar_token_invitacion,
    aceptar_invitacion,
    aceptar_invitacion_usuario_existente,
    verificar_usuario_existente,
    generar_codigo_invitacion,
    validar_codigo_invitacion,
    aceptar_invitacion_por_codigo
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
        - datos (InvitacionCreate): Nombre, email, rol, equipo, dorsal, posición, tipo de jugador
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (admin de liga o entrenador)

    Returns:
        dict: Mensaje indicando si se creó invitación o se asignó rol directamente

    Requiere autenticación: Sí
    Roles permitidos:
        - Admin de liga: puede invitar cualquier rol
        - Entrenador: solo puede invitar delegado o jugador para su equipo
    """
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol

    # Obtener el rol del usuario actual en esta liga
    usuario_rol_actual = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == current_user.id_usuario,
        UsuarioRol.id_liga == liga_id,
        UsuarioRol.activo == 1
    ).first()

    if not usuario_rol_actual:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes ningún rol en esta liga"
        )

    # Obtener nombre del rol actual
    rol_actual = db.query(Rol).filter(Rol.id_rol == usuario_rol_actual.id_rol).first()
    if not rol_actual:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no válido"
        )

    # Validar permisos según el rol del usuario que invita
    # Los nombres de roles en BD están en inglés: admin, coach, player, delegate, viewer
    if rol_actual.nombre == "admin":
        # Admin puede invitar a cualquier rol
        pass
    elif rol_actual.nombre == "coach":
        # Coach solo puede invitar delegate o player
        rol_a_asignar = db.query(Rol).filter(Rol.id_rol == datos.id_rol).first()
        if not rol_a_asignar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rol a asignar no válido"
            )
        if rol_a_asignar.nombre not in ["delegate", "player"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Como entrenador, solo puedes invitar delegados o jugadores"
            )
        # Entrenador debe especificar equipo
        if not datos.id_equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes especificar el equipo para el que se invita al usuario"
            )
        # Validar que el equipo pertenece a esta liga y que el entrenador es de ese equipo
        from app.models.equipo import Equipo
        equipo = db.query(Equipo).filter(Equipo.id_equipo == datos.id_equipo).first()
        if not equipo or equipo.id_liga != liga_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El equipo no pertenece a esta liga"
            )
        # Validar que el entrenador pertenece a este equipo
        if equipo.id_entrenador != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes invitar jugadores/delegados para tu propio equipo"
            )
    else:
        # Otros roles no pueden enviar invitaciones
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para enviar invitaciones"
        )

    # Validar campos requeridos según el rol a asignar
    rol_a_asignar = db.query(Rol).filter(Rol.id_rol == datos.id_rol).first()
    if not rol_a_asignar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol a asignar no válido"
        )

    # Validaciones por rol (nombres en inglés según BD)
    if rol_a_asignar.nombre in ["admin", "viewer"]:
        # No requieren equipo, dorsal, posición
        pass
    elif rol_a_asignar.nombre == "coach":
        # Requiere equipo
        if not datos.id_equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El entrenador debe tener un equipo asignado"
            )
    elif rol_a_asignar.nombre in ["delegate", "player"]:
        # Requieren equipo
        if not datos.id_equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este rol requiere un equipo asignado"
            )
        # Player requiere dorsal y posición
        if rol_a_asignar.nombre == "player":
            if not datos.dorsal:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El jugador debe tener un dorsal asignado"
                )
            if not datos.posicion:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El jugador debe tener una posición asignada"
                )

    # Crear invitación (tanto si el usuario existe como si no)
    # El usuario podrá aceptar la invitación mediante el enlace enviado por email
    invitacion = crear_invitacion(
        db=db,
        email=datos.email,
        id_liga=liga_id,
        id_rol=datos.id_rol,
        id_equipo=datos.id_equipo,
        dorsal=datos.dorsal,
        posicion=datos.posicion,
        tipo_jugador=datos.tipo_jugador,
        invitado_por=current_user.id_usuario,
        nombre=datos.nombre
    )

    # El email se envía dentro de crear_invitacion()

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
    datos: InvitacionAceptar | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_current_user)
):
    """
    Aceptar una invitación.

    Valida el token y:
    - Si el usuario NO existe: lo crea con los datos del formulario
    - Si el usuario YA existe (autenticado): activa el rol directamente

    Parámetros:
        - token (str): Token de invitación
        - datos (InvitacionAceptar, opcional): Email, contraseña, nombre (solo si es usuario nuevo)
        - db (Session): Sesión de base de datos
        - current_user (opcional): Usuario autenticado (si ya tiene cuenta)

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: No (solo si el usuario ya existe y está logueado)
    """
    # Validar token
    invitacion = validar_token_invitacion(db, token)

    if not invitacion["valido"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitación inválida o expirada: {invitacion.get('motivo', 'desconocido')}"
        )

    # Si el usuario ya está autenticado, usar su información
    if current_user:
        # Verificar que el email del usuario logueado coincide con la invitación
        if current_user.email.lower() != invitacion["email"].lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email de tu cuenta no coincide con la invitación"
            )

        try:
            aceptar_invitacion_usuario_existente(
                db=db,
                token=token,
                usuario_id=current_user.id_usuario
            )

            return {
                "mensaje": "Invitación aceptada correctamente. Rol activado.",
                "usuario_id": current_user.id_usuario,
                "email": current_user.email
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Usuario no autenticado - necesita registro
    if not datos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requieren datos de registro (email, password, nombre)"
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


# ============================================================
# ACEPTAR INVITACIÓN (usuario existente) - ENDPOINT LEGACY
# ============================================================

@router.post("/aceptar-existente/{token}")
def aceptar_invitacion_existente_endpoint(
    token: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Aceptar una invitación cuando el usuario ya tiene cuenta.

    Endpoint legacy para compatibilidad con tests.
    Usa el mismo flujo que /aceptar/{token} con usuario autenticado.

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


# ============================================================
# GENERAR CÓDIGO DE INVITACIÓN (solo admin de la liga)
# ============================================================

@router.post("/ligas/{liga_id}/generar-codigo", status_code=status.HTTP_201_CREATED, response_model=InvitacionCodigoResponse)
def generar_codigo_invitacion_endpoint(
    liga_id: int,
    datos: InvitacionCodigoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Genera un código corto de invitación (6-8 caracteres alfanuméricos).

    El código puede usarse UNA sola vez para unirse a la liga con el rol especificado.
    NO envía email - el código debe compartirse manualmente (chat, QR, etc.).

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - datos (InvitacionCodigoCreate): Rol, equipo, nombre opcional, dorsal, posición, tipo jugador
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (admin de liga o entrenador)

    Returns:
        InvitacionCodigoResponse:
            - codigo (str): Código alfanumérico (6-8 caracteres)
            - rol (str): Nombre del rol asignado
            - liga (str): Nombre de la liga
            - expiracion (datetime): Fecha de expiración
            - id_equipo (int | None): ID del equipo (si aplica)

    Requiere autenticación: Sí
    Roles permitidos:
        - Admin de liga: puede generar código para cualquier rol
        - Entrenador: solo delegado o jugador para su equipo
    """
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol
    from app.models.equipo import Equipo

    # Obtener el rol del usuario actual en esta liga
    usuario_rol_actual = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == current_user.id_usuario,
        UsuarioRol.id_liga == liga_id,
        UsuarioRol.activo == 1
    ).first()

    if not usuario_rol_actual:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes ningún rol en esta liga"
        )

    # Obtener nombre del rol actual
    rol_actual = db.query(Rol).filter(Rol.id_rol == usuario_rol_actual.id_rol).first()
    if not rol_actual:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no válido"
        )

    # Validar permisos según el rol del usuario que genera el código
    if rol_actual.nombre == "admin":
        # Admin puede generar código para cualquier rol
        pass
    elif rol_actual.nombre == "coach":
        # Coach solo puede generar código para delegate o player
        rol_a_asignar = db.query(Rol).filter(Rol.id_rol == datos.id_rol).first()
        if not rol_a_asignar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rol a asignar no válido"
            )
        if rol_a_asignar.nombre not in ["delegate", "player"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Como entrenador, solo puedes generar códigos para delegados o jugadores"
            )
        # Entrenador debe especificar equipo
        if not datos.id_equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes especificar el equipo para el que se genera el código"
            )
        # Validar que el equipo pertenece a esta liga y que el entrenador es de ese equipo
        equipo = db.query(Equipo).filter(Equipo.id_equipo == datos.id_equipo).first()
        if not equipo or equipo.id_liga != liga_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El equipo no pertenece a esta liga"
            )
        if equipo.id_entrenador != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes generar códigos para tu propio equipo"
            )
    else:
        # Otros roles no pueden generar códigos
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para generar códigos de invitación"
        )

    # Validaciones por rol
    rol_a_asignar = db.query(Rol).filter(Rol.id_rol == datos.id_rol).first()
    if not rol_a_asignar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol a asignar no válido"
        )

    if rol_a_asignar.nombre in ["admin", "viewer"]:
        # No requieren equipo
        pass
    elif rol_a_asignar.nombre == "coach":
        if not datos.id_equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El entrenador debe tener un equipo asignado"
            )
    elif rol_a_asignar.nombre in ["delegate", "player"]:
        if not datos.id_equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este rol requiere un equipo asignado"
            )
        if rol_a_asignar.nombre == "player":
            if not datos.dorsal:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El jugador debe tener un dorsal asignado"
                )
            if not datos.posicion:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El jugador debe tener una posición asignada"
                )

    # Generar código de invitación
    invitacion = generar_codigo_invitacion(
        db=db,
        id_liga=liga_id,
        id_rol=datos.id_rol,
        id_equipo=datos.id_equipo,
        invitado_por=current_user.id_usuario,
        nombre=datos.nombre,
        dorsal=datos.dorsal,
        posicion=datos.posicion,
        tipo_jugador=datos.tipo_jugador
    )

    # Obtener nombres para la respuesta
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    rol = db.query(Rol).filter(Rol.id_rol == datos.id_rol).first()

    return InvitacionCodigoResponse(
        codigo=invitacion.codigo,
        rol=rol.nombre if rol else "player",
        liga=liga.nombre if liga else "Liga",
        expiracion=invitacion.fecha_expiracion,
        id_equipo=datos.id_equipo
    )


# ============================================================
# VALIDAR CÓDIGO DE INVITACIÓN
# ============================================================

@router.get("/validar-codigo/{codigo}", response_model=InvitacionValidarResponse)
def validar_codigo_invitacion_endpoint(
    codigo: str,
    db: Session = Depends(get_db)
):
    """
    Validar un código corto de invitación.

    Verifica si el código existe, no está usado y no ha expirado.

    Parámetros:
        - codigo (str): Código de invitación a validar (6-8 caracteres)
        - db (Session): Sesión de base de datos

    Returns:
        InvitacionValidarResponse:
            - valido (bool): True si el código es válido
            - liga_nombre (str): Nombre de la liga (si es válido)
            - equipo_nombre (str): Nombre del equipo (si es válido)
            - rol (str): Nombre del rol (si es válido)
            - motivo (str): Motivo por el que no es válido (si no lo es)

    Requiere autenticación: No
    """
    resultado = validar_codigo_invitacion(db, codigo)

    if not resultado["valido"]:
        return InvitacionValidarResponse(
            valido=False,
            motivo=resultado.get("motivo", "Código inválido")
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
# ACEPTAR INVITACIÓN POR CÓDIGO (registro)
# ============================================================

@router.post("/aceptar-codigo/{codigo}")
def aceptar_invitacion_por_codigo_endpoint(
    codigo: str,
    datos: InvitacionAceptarCodigo,
    db: Session = Depends(get_db)
):
    """
    Aceptar una invitación mediante código corto.

    Valida el código y crea un nuevo usuario con los datos proporcionados.
    El código solo puede usarse UNA vez.

    Parámetros:
        - codigo (str): Código de invitación (6-8 caracteres)
        - datos (InvitacionAceptarCodigo): Email, contraseña, nombre
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación con usuario_id y email

    Requiere autenticación: No
    """
    # Verificar que el usuario no exista ya
    usuario_existente = db.query(Usuario).filter(Usuario.email == datos.email.lower()).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado. Inicia sesión en su lugar."
        )

    # Aceptar invitación y crear usuario
    try:
        usuario = aceptar_invitacion_por_codigo(
            db=db,
            codigo=codigo,
            email=datos.email,
            password=datos.password,
            nombre=datos.nombre
        )

        return {
            "mensaje": "Código aceptado correctamente. Usuario creado.",
            "usuario_id": usuario.id_usuario,
            "email": usuario.email
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================
# ELIMINAR CÓDIGO DE INVITACIÓN (solo admin de la liga)
# ============================================================

@router.delete("/ligas/{liga_id}/codigos/{codigo}")
def eliminar_codigo_invitacion(
    liga_id: int,
    codigo: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Eliminar/invalidar un código de invitación.

    Marca el código como usado para que no pueda utilizarse.

    Parámetros:
        - liga_id (int): ID de la liga
        - codigo (str): Código a eliminar
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (debe ser admin)

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin de la liga
    """
    from app.models.usuario_rol import UsuarioRol

    # Verificar que el usuario actual es admin de la liga
    usuario_rol_actual = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == current_user.id_usuario,
        UsuarioRol.id_liga == liga_id,
        UsuarioRol.activo == 1
    ).first()

    if not usuario_rol_actual:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes ningún rol en esta liga"
        )

    # Obtener el rol del usuario actual
    rol_actual = db.query(Rol).filter(Rol.id_rol == usuario_rol_actual.id_rol).first()
    if not rol_actual or rol_actual.nombre != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar códigos"
        )

    # Buscar la invitación por código
    invitacion = db.query(Invitacion).filter(
        Invitacion.codigo == codigo,
        Invitacion.id_liga == liga_id
    ).first()

    if not invitacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código no encontrado"
        )

    # Marcar como usada (invalidar)
    invitacion.usada = True
    db.commit()

    return {
        "mensaje": "Código eliminado correctamente",
        "codigo": codigo
    }
