"""
Servicio de lógica de negocio para Invitaciones.
Maneja la creación, validación y aceptación de invitaciones a ligas.

Puntos críticos corregidos:
- No se usa `Jugador = None`; el modelo Jugador se importa localmente solo cuando hace falta.
- Un jugador nunca se inserta con `dorsal=None`, porque `jugadores.dorsal` es INT NOT NULL.
- La creación de Usuario usa `contraseña_hash`, que es el campo real del modelo SQLAlchemy.
- Token, código y usuario existente reutilizan la misma lógica para crear/actualizar Jugador.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
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


# Roles canónicos definidos en la base de datos.
ROLE_ADMIN = "admin"
ROLE_COACH = "coach"
ROLE_DELEGATE = "delegate"
ROLE_PLAYER = "player"
ROLE_VIEWER = "viewer"

# Compatibilidad defensiva por si algún punto heredado devuelve roles en español.
ROLE_ALIASES = {
    "administrador": ROLE_ADMIN,
    "entrenador": ROLE_COACH,
    "delegado": ROLE_DELEGATE,
    "jugador": ROLE_PLAYER,
    "observador": ROLE_VIEWER,
}

DEFAULT_EXPIRATION_DAYS = 7
CODE_LENGTH_DEFAULT = 8
EMAIL_PLACEHOLDER_CODIGO = "placeholder@invitacion.codigo"


# ============================================================
# UTILIDADES INTERNAS
# ============================================================


def _now_utc() -> datetime:
    """Devuelve una fecha aware en UTC para comparar expiraciones sin errores naive/aware."""
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """Normaliza fechas de BD que puedan venir sin zona horaria."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalizar_email(email: str) -> str:
    """Evita duplicados por mayúsculas o espacios accidentales."""
    return str(email).strip().lower()


def _normalizar_rol(nombre: str | None) -> str:
    """Convierte posibles nombres heredados al nombre real usado por la BD."""
    if not nombre:
        return ""
    nombre_limpio = nombre.strip().lower()
    return ROLE_ALIASES.get(nombre_limpio, nombre_limpio)


def _get_jugador_model():
    """
    Importa Jugador de forma local.

    Esto elimina el patrón `Jugador = None`, que rompía el flujo al intentar hacer
    `db.query(Jugador)` o `Jugador(...)` sin haber importado realmente el modelo.
    """
    from app.models.jugador import Jugador

    return Jugador


def _obtener_rol(db: Session, id_rol: int) -> Rol:
    """Obtiene el rol o lanza un error claro antes de continuar."""
    rol = db.query(Rol).filter(Rol.id_rol == id_rol).first()
    if not rol:
        raise ValueError("Rol no encontrado")
    return rol


def _obtener_nombre_rol(db: Session, id_rol: int) -> str:
    """Obtiene el nombre canónico del rol desde su ID."""
    return _normalizar_rol(_obtener_rol(db, id_rol).nombre)


def _obtener_equipo_de_liga(db: Session, id_equipo: Optional[int], id_liga: int) -> Optional[Equipo]:
    """Comprueba que el equipo exista y pertenezca a la liga de la invitación."""
    if id_equipo is None:
        return None

    equipo = db.query(Equipo).filter(Equipo.id_equipo == id_equipo).first()
    if not equipo:
        raise ValueError("Equipo no encontrado")
    if equipo.id_liga != id_liga:
        raise ValueError("El equipo indicado no pertenece a la liga de la invitación")
    return equipo


def _parse_dorsal_obligatorio(raw_dorsal: Any) -> int:
    """
    Convierte dorsal a int y garantiza que no sea None.

    La tabla `jugadores` define `dorsal INT NOT NULL`; por tanto, si falta el dato
    se rechaza la operación antes de que SQLAlchemy intente insertar NULL.
    """
    if raw_dorsal is None:
        raise ValueError("El dorsal es obligatorio para crear un jugador")

    dorsal_texto = str(raw_dorsal).strip()
    if not dorsal_texto:
        raise ValueError("El dorsal es obligatorio para crear un jugador")

    try:
        dorsal = int(dorsal_texto)
    except (TypeError, ValueError):
        raise ValueError("El dorsal debe ser un número entero")

    if dorsal < 0:
        raise ValueError("El dorsal no puede ser negativo")

    return dorsal


def _validar_datos_jugador(
    db: Session,
    id_liga: int,
    id_equipo: Optional[int],
    dorsal: Optional[str],
    posicion: Optional[str],
) -> tuple[Equipo, int, str]:
    """
    Valida y normaliza los datos obligatorios para crear un Jugador.

    Devuelve equipo validado, dorsal entero y posición limpia. Esta función debe
    ejecutarse antes de crear invitaciones player y antes de aceptar invitaciones.
    """
    equipo = _obtener_equipo_de_liga(db, id_equipo, id_liga)
    if not equipo:
        raise ValueError("El equipo es obligatorio para invitar o crear un jugador")

    dorsal_int = _parse_dorsal_obligatorio(dorsal)

    posicion_limpia = (posicion or "").strip()
    if not posicion_limpia:
        raise ValueError("La posición es obligatoria para crear un jugador")

    return equipo, dorsal_int, posicion_limpia


def _validar_invitacion_jugador_si_aplica(
    db: Session,
    id_liga: int,
    id_rol: int,
    id_equipo: Optional[int],
    dorsal: Optional[str],
    posicion: Optional[str],
) -> None:
    """Valida campos deportivos solo cuando el rol invitado es player."""
    if _obtener_nombre_rol(db, id_rol) == ROLE_PLAYER:
        _validar_datos_jugador(db, id_liga, id_equipo, dorsal, posicion)


def _crear_o_actualizar_usuario_rol(
    db: Session,
    id_usuario: int,
    id_liga: int,
    id_rol: int,
    activo: int,
) -> UsuarioRol:
    """
    Crea o actualiza el rol del usuario en una liga.

    Se mantiene una única asignación por usuario/liga para evitar estados ambiguos
    en frontend: un usuario no debería aparecer dos veces con roles distintos.
    """
    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == id_usuario,
        UsuarioRol.id_liga == id_liga
    ).first()

    if asignacion:
        asignacion.id_rol = id_rol
        asignacion.activo = activo
    else:
        asignacion = UsuarioRol(
            id_usuario=id_usuario,
            id_rol=id_rol,
            id_liga=id_liga,
            activo=activo
        )
        db.add(asignacion)

    db.flush()
    return asignacion


def _crear_o_actualizar_jugador(
    db: Session,
    id_usuario: int,
    id_liga: int,
    id_equipo: Optional[int],
    dorsal: Optional[str],
    posicion: Optional[str],
):
    """
    Crea o actualiza el registro `Jugador` que luego usan las convocatorias.

    Las convocatorias trabajan con `id_jugador`, no con `id_usuario`. Si esta fila
    no existe, la convocatoria no puede listar ni seleccionar correctamente jugadores.
    """
    Jugador = _get_jugador_model()
    equipo, dorsal_int, posicion_limpia = _validar_datos_jugador(
        db=db,
        id_liga=id_liga,
        id_equipo=id_equipo,
        dorsal=dorsal,
        posicion=posicion,
    )

    jugador_existente = db.query(Jugador).filter(
        Jugador.id_usuario == id_usuario
    ).first()

    # El modelo actual marca id_usuario como unique: un usuario solo puede tener un registro jugador.
    if jugador_existente and jugador_existente.id_equipo != equipo.id_equipo:
        raise ValueError("Este usuario ya está registrado como jugador en otro equipo")

    dorsal_ocupado = db.query(Jugador).filter(
        Jugador.id_equipo == equipo.id_equipo,
        Jugador.dorsal == dorsal_int,
        Jugador.id_usuario != id_usuario,
        Jugador.activo == True
    ).first()
    if dorsal_ocupado:
        raise ValueError(f"El dorsal {dorsal_int} ya está asignado en este equipo")

    if jugador_existente:
        # Si el jugador ya existe, actualizamos datos deportivos y lo dejamos activo.
        jugador_existente.dorsal = dorsal_int
        jugador_existente.posicion = posicion_limpia
        jugador_existente.activo = True
        jugador = jugador_existente
    else:
        jugador = Jugador(
            id_usuario=id_usuario,
            id_equipo=equipo.id_equipo,
            dorsal=dorsal_int,
            posicion=posicion_limpia,
            activo=True
        )
        db.add(jugador)

    db.flush()
    return jugador


def _aplicar_relacion_equipo_si_corresponde(
    db: Session,
    id_usuario: int,
    id_liga: int,
    id_rol: int,
    id_equipo: Optional[int],
    dorsal: Optional[str],
    posicion: Optional[str],
):
    """
    Aplica la parte dependiente del equipo según el rol.

    - player: crea/actualiza Jugador.
    - coach: asigna Equipo.id_entrenador.
    - delegate: asigna Equipo.id_delegado.
    - admin/viewer: no necesitan equipo.
    """
    rol_nombre = _obtener_nombre_rol(db, id_rol)

    if rol_nombre == ROLE_PLAYER:
        return _crear_o_actualizar_jugador(
            db=db,
            id_usuario=id_usuario,
            id_liga=id_liga,
            id_equipo=id_equipo,
            dorsal=dorsal,
            posicion=posicion,
        )

    if rol_nombre in {ROLE_COACH, ROLE_DELEGATE}:
        equipo = _obtener_equipo_de_liga(db, id_equipo, id_liga)
        if not equipo:
            raise ValueError("El equipo es obligatorio para asignar entrenador o delegado")

        if rol_nombre == ROLE_COACH:
            equipo.id_entrenador = id_usuario
        else:
            equipo.id_delegado = id_usuario

        db.flush()
        return equipo

    return None


def _respuesta_validacion(invitacion: Invitacion, rol: Optional[Rol], liga: Optional[Liga], equipo: Optional[Equipo]) -> Dict[str, Any]:
    """Construye la respuesta que usa el frontend para pintar la pantalla de aceptación."""
    return {
        "valido": True,
        "email": invitacion.email,
        "nombre": invitacion.nombre,
        "liga_nombre": liga.nombre if liga else "Desconocida",
        "equipo_nombre": equipo.nombre if equipo else None,
        "rol": rol.nombre if rol else ROLE_PLAYER,
        "dorsal": invitacion.dorsal,
        "posicion": invitacion.posicion,
        "tipo_jugador": invitacion.tipo_jugador,
        "id_equipo": invitacion.id_equipo,
        "fecha_expiracion": invitacion.fecha_expiracion,
    }


def _validar_no_usada_ni_expirada(invitacion: Invitacion, tipo: str) -> Optional[Dict[str, Any]]:
    """Devuelve un error de validación si la invitación no puede usarse."""
    if invitacion.usada:
        return {"valido": False, "motivo": f"{tipo} ya utilizado"}
    if _as_utc(invitacion.fecha_expiracion) < _now_utc():
        return {"valido": False, "motivo": f"{tipo} expirado"}
    return None


def _crear_usuario(db: Session, email: str, password: str, nombre: str) -> Usuario:
    """Crea un usuario usando el campo real del modelo: contraseña_hash."""
    from app.api.services.usuario_service import hash_password

    usuario = Usuario(
        email=_normalizar_email(email),
        contraseña_hash=hash_password(password),
        nombre=nombre.strip()
    )
    db.add(usuario)
    db.flush()  # Necesario para obtener id_usuario antes de crear UsuarioRol/Jugador.
    return usuario


def _aceptar_invitacion_para_usuario(
    db: Session,
    invitacion: Invitacion,
    usuario: Usuario,
    activo: int = 1,
) -> Usuario:
    """
    Núcleo único de aceptación para token, código y usuario existente.

    Aquí se concentra la lógica que antes estaba duplicada en varias funciones y
    provocaba diferencias: unas importaban Jugador y otras no, unas validaban y otras no.
    """
    _crear_o_actualizar_usuario_rol(
        db=db,
        id_usuario=usuario.id_usuario,
        id_liga=invitacion.id_liga,
        id_rol=invitacion.id_rol,
        activo=activo,
    )

    _aplicar_relacion_equipo_si_corresponde(
        db=db,
        id_usuario=usuario.id_usuario,
        id_liga=invitacion.id_liga,
        id_rol=invitacion.id_rol,
        id_equipo=invitacion.id_equipo,
        dorsal=invitacion.dorsal,
        posicion=invitacion.posicion,
    )

    invitacion.usada = True
    db.flush()
    return usuario


# ============================================================
# FUNCIONES PÚBLICAS DEL SERVICIO
# ============================================================


def generar_token() -> str:
    """Genera un token seguro aleatorio de 32 bytes (64 caracteres hex)."""
    return secrets.token_hex(32)


def generar_codigo_unico(db: Session, longitud: int = CODE_LENGTH_DEFAULT) -> str:
    """
    Genera un código alfanumérico único de 6-8 caracteres en mayúsculas.

    Args:
        db: Sesión de base de datos.
        longitud: Longitud del código. Por defecto 8 para mantener compatibilidad.
    """
    import string

    alfabeto = string.ascii_uppercase + string.digits

    for _ in range(10):
        codigo = ''.join(secrets.choice(alfabeto) for _ in range(longitud))
        existente = db.query(Invitacion).filter(Invitacion.codigo == codigo).first()
        if not existente:
            return codigo

    raise ValueError("No se pudo generar un código único. Intente nuevamente.")


def verificar_usuario_existente(db: Session, email: str) -> Optional[Usuario]:
    """Verifica si existe un usuario con el email dado."""
    return db.query(Usuario).filter(Usuario.email == _normalizar_email(email)).first()


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

    Mantiene la firma original del proyecto. Si el rol es player, también crea o
    actualiza `Jugador` con validación estricta de equipo, dorsal y posición.
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")

        if nombre and not usuario.nombre:
            usuario.nombre = nombre.strip()

        _validar_invitacion_jugador_si_aplica(db, id_liga, id_rol, id_equipo, dorsal, posicion)

        # Se conserva el comportamiento original: queda pendiente hasta aceptación posterior.
        _crear_o_actualizar_usuario_rol(db, id_usuario, id_liga, id_rol, activo=0)

        _aplicar_relacion_equipo_si_corresponde(
            db=db,
            id_usuario=id_usuario,
            id_liga=id_liga,
            id_rol=id_rol,
            id_equipo=id_equipo,
            dorsal=dorsal,
            posicion=posicion,
        )

        db.commit()
    except Exception:
        db.rollback()
        raise


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
    Crea una nueva invitación por email.

    Antes de guardar una invitación player valida que tenga equipo, dorsal y posición,
    evitando aceptar más tarde una invitación imposible de convertir en Jugador.
    """
    try:
        _validar_invitacion_jugador_si_aplica(db, id_liga, id_rol, id_equipo, dorsal, posicion)

        token = generar_token()
        fecha_expiracion = _now_utc() + timedelta(days=DEFAULT_EXPIRATION_DAYS)

        invitacion = Invitacion(
            token=token,
            email=_normalizar_email(email),
            nombre=nombre.strip() if nombre else None,
            id_liga=id_liga,
            id_equipo=id_equipo,
            id_rol=id_rol,
            dorsal=str(dorsal).strip() if dorsal is not None else None,
            posicion=posicion.strip() if posicion else None,
            tipo_jugador=tipo_jugador,
            invitado_por=invitado_por,
            fecha_expiracion=fecha_expiracion,
            usada=False
        )

        db.add(invitacion)
        db.commit()
        db.refresh(invitacion)

        # El envío de email no debe revertir la invitación si falla el proveedor SMTP.
        try:
            liga = db.query(Liga).filter(Liga.id_liga == id_liga).first()
            rol = db.query(Rol).filter(Rol.id_rol == id_rol).first()
            equipo = db.query(Equipo).filter(Equipo.id_equipo == id_equipo).first() if id_equipo else None
            invitador = db.query(Usuario).filter(Usuario.id_usuario == invitado_por).first() if invitado_por else None

            enlace_aceptar = f"{settings.FRONTEND_URL}/register?invitation_token={token}"

            enviar_email_invitacion(
                email_destino=email,
                nombre_invitado=nombre or email.split('@')[0],
                liga_nombre=liga.nombre if liga else "Liga",
                equipo_nombre=equipo.nombre if equipo else None,
                rol=rol.nombre if rol else ROLE_PLAYER,
                dorsal=dorsal or "-",
                posicion=posicion or "-",
                tipo_jugador=tipo_jugador or "titular",
                invitador_nombre=invitador.nombre if invitador else "Administrador",
                enlace_aceptar=enlace_aceptar
            )
        except Exception as e:
            print(f"[ERROR] No se pudo enviar email de invitación: {e}")

        return invitacion
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error crítico al crear invitación: {e}")
        raise


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
    Genera un código corto de invitación sin enviar email.

    Para player, el código también debe llevar equipo, dorsal y posición porque al
    aceptar se creará la fila `jugadores` inmediatamente.
    """
    try:
        _validar_invitacion_jugador_si_aplica(db, id_liga, id_rol, id_equipo, dorsal, posicion)

        codigo = generar_codigo_unico(db)
        fecha_expiracion = _now_utc() + timedelta(days=DEFAULT_EXPIRATION_DAYS)

        invitacion = Invitacion(
            token=generar_token(),
            codigo=codigo,
            email=EMAIL_PLACEHOLDER_CODIGO,
            nombre=nombre.strip() if nombre else None,
            id_liga=id_liga,
            id_equipo=id_equipo,
            id_rol=id_rol,
            dorsal=str(dorsal).strip() if dorsal is not None else None,
            posicion=posicion.strip() if posicion else None,
            tipo_jugador=tipo_jugador,
            invitado_por=invitado_por,
            fecha_expiracion=fecha_expiracion,
            usada=False
        )

        db.add(invitacion)
        db.commit()
        db.refresh(invitacion)
        return invitacion
    except Exception:
        db.rollback()
        raise


def validar_codigo_invitacion(db: Session, codigo: str) -> Dict[str, Any]:
    """Valida un código corto de invitación."""
    invitacion = db.query(Invitacion).filter(
        Invitacion.codigo == codigo.strip().upper()
    ).first()

    if not invitacion:
        return {"valido": False, "motivo": "Código no encontrado"}

    error = _validar_no_usada_ni_expirada(invitacion, "Código")
    if error:
        return error

    liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
    rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
    equipo = db.query(Equipo).filter(Equipo.id_equipo == invitacion.id_equipo).first() if invitacion.id_equipo else None

    return _respuesta_validacion(invitacion, rol, liga, equipo)


def aceptar_invitacion_por_codigo(
    db: Session,
    codigo: str,
    email: str,
    password: str,
    nombre: str
) -> Usuario:
    """
    Acepta una invitación mediante código corto y crea usuario.

    Corrige dos errores originales: usa `contraseña_hash` y crea Jugador con dorsal
    obligatorio validado, no con `None`.
    """
    try:
        validacion = validar_codigo_invitacion(db, codigo)
        if not validacion["valido"]:
            raise ValueError(f"Código inválido: {validacion.get('motivo', 'desconocido')}")

        email_normalizado = _normalizar_email(email)
        usuario_existente = db.query(Usuario).filter(Usuario.email == email_normalizado).first()
        if usuario_existente:
            raise ValueError("El email ya está registrado. Inicia sesión en su lugar.")

        invitacion = db.query(Invitacion).filter(Invitacion.codigo == codigo.strip().upper()).first()
        if not invitacion:
            raise ValueError("Invitación no encontrada")

        usuario = _crear_usuario(db, email_normalizado, password, nombre)

        # En códigos cortos se reemplaza el email placeholder por el email real usado al registrarse.
        invitacion.email = email_normalizado
        if nombre:
            invitacion.nombre = nombre.strip()

        _aceptar_invitacion_para_usuario(db, invitacion, usuario, activo=1)
        db.commit()
        db.refresh(usuario)
        return usuario
    except (ValueError, IntegrityError):
        db.rollback()
        raise


def aceptar_invitacion_por_codigo_usuario_existente(
    db: Session,
    codigo: str,
    usuario_id: int
) -> Usuario:
    """Acepta una invitación mediante código corto cuando el usuario ya tiene cuenta."""
    try:
        validacion = validar_codigo_invitacion(db, codigo)
        if not validacion["valido"]:
            raise ValueError(f"Código inválido: {validacion.get('motivo', 'desconocido')}")

        invitacion = db.query(Invitacion).filter(Invitacion.codigo == codigo.strip().upper()).first()
        if not invitacion:
            raise ValueError("Invitación no encontrada")

        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")

        usuario_rol_activo = db.query(UsuarioRol).filter(
            UsuarioRol.id_usuario == usuario_id,
            UsuarioRol.id_liga == invitacion.id_liga,
            UsuarioRol.activo == 1
        ).first()
        if usuario_rol_activo:
            raise ValueError("Ya tienes un rol activo en esta liga")

        # En códigos cortos no había email real. Al aceptar con sesión, lo fijamos.
        invitacion.email = usuario.email
        _aceptar_invitacion_para_usuario(db, invitacion, usuario, activo=1)

        db.commit()
        db.refresh(usuario)
        return usuario
    except (ValueError, IntegrityError):
        db.rollback()
        raise


def validar_token_invitacion(db: Session, token: str) -> Dict[str, Any]:
    """Valida un token de invitación enviado por email."""
    invitacion = db.query(Invitacion).filter(Invitacion.token == token).first()

    if not invitacion:
        return {"valido": False, "motivo": "Token no encontrado"}

    error = _validar_no_usada_ni_expirada(invitacion, "Invitación")
    if error:
        return error

    liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
    rol = db.query(Rol).filter(Rol.id_rol == invitacion.id_rol).first()
    equipo = db.query(Equipo).filter(Equipo.id_equipo == invitacion.id_equipo).first() if invitacion.id_equipo else None

    return _respuesta_validacion(invitacion, rol, liga, equipo)


def aceptar_invitacion(
    db: Session,
    token: str,
    email: str,
    password: str | None = None,
    nombre: str | None = None
) -> Usuario:
    """
    Acepta una invitación por token.

    Si el usuario existe, reutiliza el flujo de usuario existente. Si no existe,
    crea el usuario y las entidades dependientes necesarias para convocatorias.
    """
    try:
        validacion = validar_token_invitacion(db, token)
        if not validacion["valido"]:
            raise ValueError(f"Invitación inválida: {validacion.get('motivo', 'desconocido')}")

        invitacion = db.query(Invitacion).filter(Invitacion.token == token).first()
        if not invitacion:
            raise ValueError("Invitación no encontrada")

        email_normalizado = _normalizar_email(email)
        if email_normalizado != _normalizar_email(invitacion.email):
            raise ValueError("El email no coincide con la invitación")

        usuario = db.query(Usuario).filter(Usuario.email == email_normalizado).first()
        if usuario:
            db.rollback()  # Cierra cualquier estado parcial antes de delegar en el flujo existente.
            return aceptar_invitacion_usuario_existente(db, token, usuario.id_usuario)

        if not password or not nombre:
            raise ValueError("Se requiere contraseña y nombre para usuarios nuevos")

        usuario = _crear_usuario(db, email_normalizado, password, nombre)
        _aceptar_invitacion_para_usuario(db, invitacion, usuario, activo=1)

        db.commit()
        db.refresh(usuario)
        return usuario
    except (ValueError, IntegrityError):
        db.rollback()
        raise


def aceptar_invitacion_usuario_existente(
    db: Session,
    token: str,
    usuario_id: int
) -> bool:
    """Acepta una invitación por token cuando el usuario ya tiene cuenta."""
    try:
        validacion = validar_token_invitacion(db, token)
        if not validacion["valido"]:
            raise ValueError(f"Invitación inválida: {validacion.get('motivo', 'desconocido')}")

        usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")

        invitacion = db.query(Invitacion).filter(Invitacion.token == token).first()
        if not invitacion:
            raise ValueError("Invitación no encontrada")

        if _normalizar_email(usuario.email) != _normalizar_email(invitacion.email):
            raise ValueError("El email no coincide con la invitación")

        liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
        if not liga:
            raise ValueError("Liga no encontrada")

        usuario_rol_activo = db.query(UsuarioRol).filter(
            UsuarioRol.id_usuario == usuario_id,
            UsuarioRol.id_liga == invitacion.id_liga,
            UsuarioRol.activo == 1
        ).first()
        if usuario_rol_activo:
            raise ValueError(f"Ya perteneces a una liga con el nombre '{liga.nombre}'")

        _aceptar_invitacion_para_usuario(db, invitacion, usuario, activo=1)

        db.commit()
        return True
    except (ValueError, IntegrityError):
        db.rollback()
        raise
