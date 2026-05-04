"""
Servicio de lógica de negocio para Invitaciones.
Maneja la creación, validación y aceptación de invitaciones a ligas.
Soporta dos métodos de invitación:
- Token UUID (64 chars hex) - enviado por email
- Código corto (6-8 chars alfanuméricos) - generado sin email
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from typing import Optional, Dict, Any

from app.models.invitacion import Invitacion
from app.models.liga import Liga
from app.models.equipo import Equipo
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.api.services.email_service import enviar_email_invitacion
from app.config import settings

# Importación diferida para evitar circular import
Jugador = None  # Se importa cuando se necesita


def generar_token() -> str:
    """Genera un token seguro aleatorio de 32 bytes (64 caracteres hex)."""
    return secrets.token_hex(32)


def generar_codigo_unico(db: Session, longitud: int = 8) -> str:
    """
    Genera un código alfanumérico único de 6-8 caracteres (mayúsculas).

    Args:
        db: Sesión de base de datos
        longitud: Longitud del código (default: 8)

    Returns:
        str: Código alfanumérico único

    Raises:
        ValueError: Si no puede generar un código único tras 10 intentos
    """
    import string

    alfabeto = string.ascii_uppercase + string.digits  # A-Z, 0-9

    for _ in range(10):  # Máximo 10 intentos
        codigo = ''.join(secrets.choice(alfabeto) for _ in range(longitud))

        # Verificar unicidad
        existente = db.query(Invitacion).filter(Invitacion.codigo == codigo).first()
        if not existente:
            return codigo

    raise ValueError("No se pudo generar un código único. Intente nuevamente.")


def verificar_usuario_existente(db: Session, email: str) -> Optional[Usuario]:
    """
    Verifica si existe un usuario con el email dado.

    Args:
        db: Sesión de base de datos
        email: Email a buscar

    Returns:
        Usuario si existe, None si no
    """
    return db.query(Usuario).filter(Usuario.email == email.lower()).first()


def asignar_rol_directamente(
    db: Session,
    id_usuario: int,
    id_liga: int,
    id_rol: int,
    id_equipo: Optional[int] = None,
    dorsal: Optional[str] = None,
    posicion: Optional[str] = None,
    tipo_jugador: Optional[str] = None,
    nombre: Optional[str] = None
) -> None:
    """
    Asigna un rol a un usuario existente en una liga.

    Args:
        db: Sesión de base de datos
        id_usuario: ID del usuario
        id_liga: ID de la liga
        id_rol: ID del rol a asignar
        id_equipo: ID del equipo (opcional)
        dorsal: Dorsal asignado (opcional)
        posicion: Posición del jugador (opcional)
        tipo_jugador: Tipo de jugador (opcional)
        nombre: Nombre del usuario (para actualizar si no tiene)
    """
    # Verificar si el usuario ya tiene alguna asignación en esta liga
    asignacion_existente = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == id_usuario,
        UsuarioRol.id_liga == id_liga
    ).first()

    if asignacion_existente:
        # Actualizar el rol al nuevo rol especificado
        asignacion_existente.id_rol = id_rol
        asignacion_existente.activo = 0  # Pendiente hasta que el usuario acepte
        db.commit()
    else:
        # Crear nueva asignación
        usuario_rol = UsuarioRol(
            id_usuario=id_usuario,
            id_rol=id_rol,
            id_liga=id_liga,
            activo=0  # Pendiente hasta que el usuario acepte
        )
        db.add(usuario_rol)
        db.commit()

    # Si es rol jugador y hay equipo, crear entrada en Jugador
    rol = db.query(Rol).filter(Rol.id_rol == id_rol).first()
    if rol and rol.nombre == "player" and id_equipo:
        # Verificar si ya existe el jugador
        jugador_existente = db.query(Jugador).filter(
            Jugador.id_usuario == id_usuario,
            Jugador.id_equipo == id_equipo
        ).first()
        if not jugador_existente:
            # Convertir dorsal de string a int (la invitación lo guarda como VARCHAR, pero Jugador requiere INT)
            dorsal_int = int(dorsal) if dorsal else None
            jugador = Jugador(
                id_usuario=id_usuario,
                id_equipo=id_equipo,
                dorsal=dorsal_int,
                posicion=posicion,
                tipo_jugador=tipo_jugador or "titular"
            )
            db.add(jugador)
            db.commit()


def crear_invitacion(
    db: Session,
    email: str,
    id_liga: int,
    id_rol: int,
    id_equipo: Optional[int] = None,
    dorsal: Optional[str] = None,
    posicion: Optional[str] = None,
    tipo_jugador: Optional[str] = None,
    invitado_por: Optional[int] = None,
    nombre: Optional[str] = None
) -> Invitacion:
    """
    Crea una nueva invitación en la base de datos.

    Genera un token único, calcula la fecha de expiración (7 días) y guarda
    la invitación.

    Args:
        db: Sesión de base de datos
        email: Email del usuario invitado
        id_liga: ID de la liga
        id_rol: ID del rol a asignar
        id_equipo: ID del equipo (opcional)
        dorsal: Dorsal asignado (opcional)
        posicion: Posición del jugador (opcional)
        tipo_jugador: Tipo de jugador (opcional)
        invitado_por: ID del usuario que envía la invitación (opcional)
        nombre: Nombre completo del usuario invitado (opcional)

    Returns:
        Invitacion: Objeto Invitacion creado con su token
    """
    # Generar token único
    token = generar_token()

    # Calcular fecha de expiración (7 días desde ahora)
    fecha_expiracion = datetime.utcnow() + timedelta(days=7)

    # Crear invitación
    invitacion = Invitacion(
        token=token,
        email=email.lower().strip(),
        nombre=nombre,
        id_liga=id_liga,
        id_equipo=id_equipo,
        id_rol=id_rol,
        dorsal=dorsal,
        posicion=posicion,
        tipo_jugador=tipo_jugador,
        invitado_por=invitado_por,
        fecha_expiracion=fecha_expiracion,
        usada=False
    )

    db.add(invitacion)
    db.commit()
    db.refresh(invitacion)

    # Enviar email de invitación
    try:
        # Obtener nombres para el email
        liga = db.query(Liga).filter(Liga.id_liga == id_liga).first()
        rol = db.query(Rol).filter(Rol.id_rol == id_rol).first()
        equipo = None
        if id_equipo:
            equipo = db.query(Equipo).filter(Equipo.id_equipo == id_equipo).first()

        invitador = None
        if invitado_por:
            invitador = db.query(Usuario).filter(Usuario.id_usuario == invitado_por).first()

        enlace_aceptar = f"{settings.FRONTEND_URL}/register?invitation_token={token}"

        enviar_email_invitacion(
            email_destino=email,
            nombre_invitado=nombre or email.split('@')[0],  # Usar nombre proporcionado o parte local del email
            liga_nombre=liga.nombre if liga else "Liga",
            equipo_nombre=equipo.nombre if equipo else None,
            rol=rol.nombre if rol else "player",
            dorsal=dorsal or "-",
            posicion=posicion or "-",
            tipo_jugador=tipo_jugador or "titular",
            invitador_nombre=invitador.nombre if invitador else "Administrador",
            enlace_aceptar=enlace_aceptar
        )
    except Exception as e:
        # Log error pero no fallar la creación de invitación
        print(f"[ERROR] No se pudo enviar email de invitación: {e}")

    return invitacion


def generar_codigo_invitacion(
    db: Session,
    id_liga: int,
    id_rol: int,
    id_equipo: Optional[int] = None,
    invitado_por: Optional[int] = None,
    nombre: Optional[str] = None,
    dorsal: Optional[str] = None,
    posicion: Optional[str] = None,
    tipo_jugador: Optional[str] = None
) -> Invitacion:
    """
    Genera un código corto de invitación SIN enviar email.

    Crea una invitación con código alfanumérico único (6-8 caracteres)
    que puede ser usado UNA sola vez. NO envía email automáticamente.

    Args:
        db: Sesión de base de datos
        id_liga: ID de la liga
        id_rol: ID del rol a asignar
        id_equipo: ID del equipo (opcional)
        invitado_por: ID del usuario que genera el código (opcional)
        nombre: Nombre opcional del invitado
        dorsal: Dorsal asignado (opcional)
        posicion: Posición del jugador (opcional)
        tipo_jugador: Tipo de jugador (opcional)

    Returns:
        Invitacion: Objeto Invitacion creado con su código

    Raises:
        ValueError: Si no puede generar un código único
    """
    # Generar código único
    codigo = generar_codigo_unico(db)

    # Calcular fecha de expiración (7 días desde ahora)
    fecha_expiracion = datetime.utcnow() + timedelta(days=7)

    # Crear invitación con código (email requerido pero puede ser placeholder)
    invitacion = Invitacion(
        token=generar_token(),  # Token UUID también se genera para compatibilidad
        codigo=codigo,
        email="placeholder@invitacion.codigo",  # Placeholder - no se usa email
        nombre=nombre,
        id_liga=id_liga,
        id_equipo=id_equipo,
        id_rol=id_rol,
        dorsal=dorsal,
        posicion=posicion,
        tipo_jugador=tipo_jugador,
        invitado_por=invitado_por,
        fecha_expiracion=fecha_expiracion,
        usada=False
    )

    db.add(invitacion)
    db.commit()
    db.refresh(invitacion)

    return invitacion


def validar_codigo_invitacion(db: Session, codigo: str) -> Dict[str, Any]:
    """
    Valida un código corto de invitación.

    Verifica que el código exista, no esté usado y no haya expirado.

    Args:
        db: Sesión de base de datos
        codigo: Código a validar

    Returns:
        Dict con:
            - valido (bool): True si es válido
            - motivo (str): Motivo si no es válido
            - email, liga_nombre, equipo_nombre, rol, etc. si es válido
    """
    # Buscar invitación por código
    invitacion = db.query(Invitacion).filter(Invitacion.codigo == codigo).first()

    if not invitacion:
        return {"valido": False, "motivo": "Código no encontrado"}

    if invitacion.usada:
        return {"valido": False, "motivo": "Código ya utilizado"}

    if invitacion.fecha_expiracion < datetime.utcnow():
        return {"valido": False, "motivo": "Código expirado"}

    # Código válido, obtener información adicional
    liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
    rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
    equipo = None
    if invitacion.id_equipo:
        equipo = db.query(Equipo).filter(Equipo.id_equipo == invitacion.id_equipo).first()

    return {
        "valido": True,
        "email": invitacion.email,
        "nombre": invitacion.nombre,
        "liga_nombre": liga.nombre if liga else "Desconocida",
        "equipo_nombre": equipo.nombre if equipo else None,
        "rol": rol.nombre if rol else "player",
        "dorsal": invitacion.dorsal,
        "posicion": invitacion.posicion,
        "tipo_jugador": invitacion.tipo_jugador,
        "id_equipo": invitacion.id_equipo,
        "fecha_expiracion": invitacion.fecha_expiracion
    }


def aceptar_invitacion_por_codigo(
    db: Session,
    codigo: str,
    email: str,
    password: str,
    nombre: str
) -> Usuario:
    """
    Acepta una invitación mediante código corto y crea usuario.

    Valida el código, verifica que el usuario no exista,
    crea el usuario y asigna el rol.

    Args:
        db: Sesión de base de datos
        codigo: Código de la invitación
        email: Email del usuario
        password: Contraseña del usuario
        nombre: Nombre del usuario

    Returns:
        Usuario: Usuario creado

    Raises:
        ValueError: Si el código es inválido o usuario ya existe
    """
    # Validar código
    validacion = validar_codigo_invitacion(db, codigo)
    if not validacion["valido"]:
        raise ValueError(f"Código inválido: {validacion.get('motivo', 'desconocido')}")

    # Verificar que el usuario no exista ya
    usuario_existente = db.query(Usuario).filter(Usuario.email == email.lower()).first()
    if usuario_existente:
        raise ValueError("El email ya está registrado. Inicia sesión en su lugar.")

    # Obtener invitación completa
    invitacion = db.query(Invitacion).filter(Invitacion.codigo == codigo).first()
    if not invitacion:
        raise ValueError("Invitación no encontrada")

    # Crear nuevo usuario
    from app.api.services.usuario_service import hash_password
    usuario = Usuario(
        email=email.lower().strip(),
        password=hash_password(password),
        nombre=nombre.strip()
    )
    db.add(usuario)
    db.flush()

    # Asignar rol activo
    usuario_rol = UsuarioRol(
        id_usuario=usuario.id_usuario,
        id_rol=invitacion.id_rol,
        id_liga=invitacion.id_liga,
        activo=1
    )
    db.add(usuario_rol)

    # Si es jugador con equipo, crear entrada
    if invitacion.id_equipo and invitacion.id_rol:
        rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
        if rol and rol.nombre == "player":
            from app.models.jugador import Jugador
            # Convertir dorsal de string a int (la invitación lo guarda como VARCHAR, pero Jugador requiere INT)
            dorsal_int = int(invitacion.dorsal) if invitacion.dorsal else None
            jugador = Jugador(
                id_usuario=usuario.id_usuario,
                id_equipo=invitacion.id_equipo,
                dorsal=dorsal_int,
                posicion=invitacion.posicion,
                tipo_jugador=invitacion.tipo_jugador or "titular"
            )
            db.add(jugador)

    # Marcar invitación como usada
    invitacion.usada = True
    db.commit()
    db.refresh(usuario)

    return usuario


def validar_token_invitacion(db: Session, token: str) -> Dict[str, Any]:
    """
    Valida un token de invitación.

    Verifica que el token exista, no esté usado y no haya expirado.

    Args:
        db: Sesión de base de datos
        token: Token a validar

    Returns:
        Dict con:
            - valido (bool): True si es válido
            - motivo (str): Motivo si no es válido
            - email, liga_nombre, equipo_nombre, rol, etc. si es válido
    """
    # Buscar invitación por token
    invitacion = db.query(Invitacion).filter(Invitacion.token == token).first()

    if not invitacion:
        return {"valido": False, "motivo": "Token no encontrado"}

    if invitacion.usada:
        return {"valido": False, "motivo": "Invitación ya utilizada"}

    if invitacion.fecha_expiracion < datetime.utcnow():
        return {"valido": False, "motivo": "Invitación expirada"}

    # Token válido, obtener información adicional
    liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
    rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
    equipo = None
    if invitacion.id_equipo:
        equipo = db.query(Equipo).filter(Equipo.id_equipo == invitacion.id_equipo).first()

    return {
        "valido": True,
        "email": invitacion.email,
        "nombre": invitacion.nombre,
        "liga_nombre": liga.nombre if liga else "Desconocida",
        "equipo_nombre": equipo.nombre if equipo else None,
        "rol": rol.nombre if rol else "player",
        "dorsal": invitacion.dorsal,
        "posicion": invitacion.posicion,
        "tipo_jugador": invitacion.tipo_jugador
    }


def aceptar_invitacion(
    db: Session,
    token: str,
    email: str,
    password: str | None = None,
    nombre: str | None = None
) -> Usuario:
    """
    Acepta una invitación y crea/activa el usuario.

    Valida el token, y:
    - Si el usuario NO existe: lo crea con contraseña y asigna rol activo
    - Si el usuario YA existe: activa/asigna el rol en la liga

    Args:
        db: Sesión de base de datos
        token: Token de la invitación
        email: Email del usuario
        password: Contraseña (solo si es usuario nuevo)
        nombre: Nombre del usuario (solo si es usuario nuevo)

    Returns:
        Usuario: Usuario creado o existente

    Raises:
        ValueError: Si el token es inválido
    """
    # Validar token
    validacion = validar_token_invitacion(db, token)
    if not validacion["valido"]:
        raise ValueError(f"Invitación inválida: {validacion.get('motivo', 'desconocido')}")

    # Obtener invitación completa
    invitacion = db.query(Invitacion).filter(Invitacion.token == token).first()
    if not invitacion:
        raise ValueError("Invitación no encontrada")

    # Verificar si el usuario ya existe
    usuario = db.query(Usuario).filter(Usuario.email == email.lower()).first()

    if usuario:
        # Usuario YA existe - solo activar/asignar rol
        return aceptar_invitacion_usuario_existente(db, token, usuario.id_usuario)

    # Usuario NUEVO - crear con contraseña
    if not password or not nombre:
        raise ValueError("Se requiere contraseña y nombre para usuarios nuevos")

    from app.api.services.usuario_service import hash_password
    usuario = Usuario(
        email=email.lower().strip(),
        password=hash_password(password),
        nombre=nombre.strip()
    )
    db.add(usuario)
    db.flush()

    # Asignar rol activo
    usuario_rol = UsuarioRol(
        id_usuario=usuario.id_usuario,
        id_rol=invitacion.id_rol,
        id_liga=invitacion.id_liga,
        activo=1
    )
    db.add(usuario_rol)

    # Si es jugador con equipo, crear entrada
    if invitacion.id_equipo and invitacion.id_rol:
        rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
        if rol and rol.nombre == "player":
            # Convertir dorsal de string a int (la invitación lo guarda como VARCHAR, pero Jugador requiere INT)
            dorsal_int = int(invitacion.dorsal) if invitacion.dorsal else None
            jugador = Jugador(
                id_usuario=usuario.id_usuario,
                id_equipo=invitacion.id_equipo,
                dorsal=dorsal_int,
                posicion=invitacion.posicion,
                tipo_jugador=invitacion.tipo_jugador or "titular"
            )
            db.add(jugador)

    invitacion.usada = True
    db.commit()
    db.refresh(usuario)

    return usuario


def aceptar_invitacion_usuario_existente(
    db: Session,
    token: str,
    usuario_id: int
) -> bool:
    """
    Acepta una invitación cuando el usuario ya tiene cuenta.

    Valida el token, asigna/actualiza el rol del usuario en la liga
    y marca la invitación como usada.

    Args:
        db: Sesión de base de datos
        token: Token de la invitación
        usuario_id: ID del usuario que acepta

    Returns:
        bool: True si se aceptó correctamente

    Raises:
        ValueError: Si el token es inválido, el email no coincide,
                   o el usuario ya pertenece a la misma liga
    """
    # Validar token
    validacion = validar_token_invitacion(db, token)
    if not validacion["valido"]:
        raise ValueError(f"Invitación inválida: {validacion.get('motivo', 'desconocido')}")

    # Obtener usuario
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Verificar que el email coincide
    if usuario.email.lower() != validacion["email"].lower():
        raise ValueError("El email no coincide con la invitación")

    # Obtener invitación
    invitacion = db.query(Invitacion).filter(Invitacion.token == token).first()
    if not invitacion:
        raise ValueError("Invitación no encontrada")

    # Obtener liga
    liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
    if not liga:
        raise ValueError("Liga no encontrada")

    # Verificar si el usuario ya tiene un rol activo en esta liga
    usuario_rol_activo = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == invitacion.id_liga,
        UsuarioRol.activo == 1
    ).first()

    if usuario_rol_activo:
        # El usuario ya pertenece activamente a esta liga
        raise ValueError(f"Ya perteneces a una liga con el nombre '{liga.nombre}'")

    # Verificar si existe asignación (activa o no) en esta liga
    asignacion_existente = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == invitacion.id_liga
    ).first()

    if asignacion_existente:
        # Actualizar al rol de la invitación y activar
        asignacion_existente.id_rol = invitacion.id_rol
        asignacion_existente.activo = 1
    else:
        # Crear nueva asignación activa con el rol de la invitación
        usuario_rol = UsuarioRol(
            id_usuario=usuario_id,
            id_rol=invitacion.id_rol,
            id_liga=invitacion.id_liga,
            activo=1
        )
        db.add(usuario_rol)

    # Si hay equipo, actualizar el equipo del jugador (si es rol player)
    if invitacion.id_equipo and invitacion.id_rol:
        rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
        if rol and rol.nombre == "player":
            # Crear jugador asociado al equipo
            from app.models.jugador import Jugador
            # Convertir dorsal de string a int (la invitación lo guarda como VARCHAR, pero Jugador requiere INT)
            dorsal_int = int(invitacion.dorsal) if invitacion.dorsal else None
            jugador = Jugador(
                id_usuario=usuario_id,
                id_equipo=invitacion.id_equipo,
                dorsal=dorsal_int,
                posicion=invitacion.posicion,
                tipo_jugador=invitacion.tipo_jugador or "titular"
            )
            db.add(jugador)

    # Marcar invitación como usada
    invitacion.usada = True
    db.commit()

    return True
