"""
Servicios de lógica de negocio para Usuario.
Maneja operaciones CRUD de usuarios, autenticación, gestión de contraseñas
con hashing bcrypt, y asignación de roles.
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets

from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.models.rol import Rol
from app.models.token_recuperacion import TokenRecuperacion
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.config import settings

# Configuración del contexto de hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# UTILIDADES
# ============================================================


def hash_password(password: str) -> str:
    """
    Genera un hash seguro de una contraseña usando bcrypt.
    
    Args:
        password (str): Contraseña en texto plano
    
    Returns:
        str: Hash de la contraseña
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash.
    
    Args:
        password (str): Contraseña en texto plano a verificar
        hashed (str): Hash almacenado de la contraseña
    
    Returns:
        bool: True si la contraseña es correcta, False en caso contrario
    """
    return pwd_context.verify(password, hashed)

# ============================================================
# AUTENTICACIÓN
# ============================================================


def autenticar_usuario(db: Session, email: str, password: str):
    """
    Autentica un usuario mediante email y contraseña.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        email (str): Email del usuario
        password (str): Contraseña en texto plano
    
    Returns:
        Usuario: Objeto Usuario si las credenciales son correctas, None en caso contrario
    """
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return None
    # Verificar contraseña
    if not verify_password(password, usuario.contraseña_hash):
        return None
    return usuario

# ============================================================
# CRUD USUARIOS
# ============================================================


def crear_usuario(db: Session, datos: UsuarioCreate):
    """
    Crea un nuevo usuario en el sistema.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (UsuarioCreate): Datos del usuario (nombre, email, contraseña)
    
    Returns:
        Usuario: Objeto Usuario creado con su ID asignado
    
    Raises:
        ValueError: Si el email ya está registrado
    """
    # Verificar que el email sea único
    existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existente:
        raise ValueError("El email ya está registrado")

    usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        contraseña_hash=hash_password(datos.password)
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario


def obtener_usuarios(db: Session):
    """
    Obtiene todos los usuarios registrados.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
    
    Returns:
        list[Usuario]: Lista con todos los usuarios
    """
    return db.query(Usuario).all()


def obtener_usuario_por_id(db: Session, usuario_id: int):
    """
    Busca un usuario por su ID.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario a buscar

    Returns:
        Usuario: Objeto Usuario si existe, None si no se encuentra
    """
    return db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()


def obtener_usuario_por_id_con_roles(db: Session, usuario_id: int):
    """
    Busca un usuario por su ID incluyendo sus roles (eager loading).

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario a buscar

    Returns:
        Usuario: Objeto Usuario con roles cargados si existe, None si no se encuentra
    """
    from sqlalchemy.orm import joinedload
    return db.query(Usuario).options(
        joinedload(Usuario.roles)
    ).filter(Usuario.id_usuario == usuario_id).first()


def actualizar_usuario(db: Session, usuario_id: int, datos: UsuarioUpdate):
    """
    Actualiza los datos de un usuario existente.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario a actualizar
        datos (UsuarioUpdate): Datos a actualizar (nombre, email, contraseña, genero, telefono, fecha_nacimiento)

    Returns:
        Usuario: Objeto Usuario actualizado

    Raises:
        ValueError: Si el usuario no existe o el email ya está en uso
    """
    usuario = obtener_usuario_por_id(db, usuario_id)
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Actualizar nombre
    if datos.nombre is not None:
        usuario.nombre = datos.nombre

    # Actualizar email
    if datos.email is not None:
        # Verificar que el nuevo email sea único (excluyendo el usuario actual)
        existente = db.query(Usuario).filter(
            Usuario.email == datos.email,
            Usuario.id_usuario != usuario_id
        ).first()
        if existente:
            raise ValueError("El email ya está en uso")
        usuario.email = datos.email

    # Actualizar contraseña
    password_value = getattr(datos, 'password', None) or getattr(datos, 'contraseña', None)
    if password_value is not None:
        usuario.contraseña_hash = hash_password(password_value)

    # Actualizar género
    if datos.genero is not None:
        usuario.genero = datos.genero

    # Actualizar teléfono
    if datos.telefono is not None:
        usuario.telefono = datos.telefono

    # Actualizar fecha de nacimiento
    if datos.fecha_nacimiento is not None:
        usuario.fecha_nacimiento = datos.fecha_nacimiento

    # Actualizar imagen_url
    if hasattr(datos, 'imagen_url') and datos.imagen_url is not None:
        usuario.imagen_url = datos.imagen_url

    db.commit()
    db.refresh(usuario)
    return usuario


def eliminar_usuario(db: Session, usuario_id: int):
    """
    Elimina un usuario del sistema.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario a eliminar
    
    Raises:
        ValueError: Si el usuario no existe
    """
    usuario = obtener_usuario_por_id(db, usuario_id)
    if not usuario:
        raise ValueError("Usuario no encontrado")

    db.delete(usuario)
    db.commit()

# ============================================================
# ROLES
# ============================================================


def asignar_rol_a_usuario(db: Session, usuario_id: int, rol_id: int, id_liga: int = None):
    """
    Asigna un rol a un usuario en una liga específica.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        rol_id (int): ID del rol a asignar
        id_liga (int): ID de la liga donde aplica el rol (requerido)

    Returns:
        bool: True si se asignó correctamente

    Raises:
        ValueError: Si el usuario, rol o liga no existe, o si el usuario ya tiene ese rol en esa liga
    """
    from app.models.liga import Liga

    # Verificar que el usuario existe
    usuario = obtener_usuario_por_id(db, usuario_id)
    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Verificar que el rol existe
    rol = db.query(Rol).filter(Rol.id_rol == rol_id).first()
    if not rol:
        raise ValueError("Rol no encontrado")

    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == id_liga).first()
    if not liga:
        raise ValueError("Liga no encontrada")

    # Evitar asignaciones duplicadas para la misma liga
    existente = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_rol == rol_id,
        UsuarioRol.id_liga == id_liga
    ).first()

    if existente:
        raise ValueError("El usuario ya tiene este rol en esta liga")

    # Crear la asignación
    asignacion = UsuarioRol(id_usuario=usuario_id, id_rol=rol_id, id_liga=id_liga)
    db.add(asignacion)
    db.commit()
    return True

# ============================================================
# RECUPERACIÓN DE CONTRASEÑA
# ============================================================


def obtener_usuario_por_email(db: Session, email: str):
    """
    Busca un usuario por su email.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        email (str): Email del usuario a buscar

    Returns:
        Usuario: Objeto Usuario si existe, None si no se encuentra
    """
    return db.query(Usuario).filter(Usuario.email == email).first()


def crear_token_recuperacion(db: Session, usuario_id: int) -> str:
    """
    Crea un token de recuperación de contraseña para un usuario.

    Genera un token seguro usando secrets.token_urlsafe y lo almacena
    en la base de datos con una fecha de expiración configurable.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario que solicita recuperación

    Returns:
        str: Token de recuperación generado
    """
    # Generar token seguro
    token = secrets.token_urlsafe(32)

    # Calcular fecha de expiración
    fecha_expiracion = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

    # Crear registro en base de datos
    token_recuperacion = TokenRecuperacion(
        id_usuario=usuario_id,
        token=token,
        fecha_expiracion=fecha_expiracion,
        usado=False
    )

    db.add(token_recuperacion)
    db.commit()
    db.refresh(token_recuperacion)

    return token


def validar_token_recuperacion(db: Session, token: str) -> Usuario | None:
    """
    Valida un token de recuperación de contraseña.

    Verifica que el token:
    - Exista en la base de datos
    - No haya expirado
    - No haya sido usado anteriormente

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        token (str): Token de recuperación a validar

    Returns:
        Usuario: Objeto Usuario si el token es válido, None en caso contrario
    """
    # Buscar token en la base de datos
    token_db = db.query(TokenRecuperacion).filter(
        TokenRecuperacion.token == token,
        TokenRecuperacion.usado == False,
        TokenRecuperacion.fecha_expiracion > datetime.utcnow()
    ).first()

    if not token_db:
        return None

    # Obtener el usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id_usuario == token_db.id_usuario).first()

    return usuario


def marcar_token_usado(db: Session, token: str) -> bool:
    """
    Marca un token de recuperación como usado.

    Invalida el token después de que el usuario ha cambiado su contraseña.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        token (str): Token de recuperación a invalidar

    Returns:
        bool: True si se marcó correctamente, False si no se encontró
    """
    token_db = db.query(TokenRecuperacion).filter(TokenRecuperacion.token == token).first()

    if not token_db:
        return False

    token_db.usado = True
    db.commit()

    return True


def cambiar_contrasena_usuario(db: Session, usuario_id: int, nueva_contrasena: str) -> bool:
    """
    Cambia la contraseña de un usuario.

    Hashea la nueva contraseña y actualiza el registro del usuario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        nueva_contrasena (str): Nueva contraseña en texto plano

    Returns:
        bool: True si se cambió correctamente
    """
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()

    if not usuario:
        return False

    usuario.contraseña_hash = hash_password(nueva_contrasena)
    db.commit()

    return True

# ============================================================
# SEGUIMIENTO DE LIGAS
# ============================================================


def seguir_liga(db: Session, usuario_id: int, liga_id: int):
    """
    Permite a un usuario seguir una liga.

    Crea una relación de seguimiento entre el usuario y la liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        liga_id (int): ID de la liga a seguir

    Returns:
        UsuarioSigueLiga: Objeto de seguimiento creado

    Raises:
        ValueError: Si el usuario ya sigue la liga o si la liga no existe
    """
    from app.models.usuario_sigue_liga import UsuarioSigueLiga
    from app.models.liga import Liga

    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise ValueError("Liga no encontrada")

    # Verificar que el usuario no siga ya la liga
    existente = db.query(UsuarioSigueLiga).filter(
        UsuarioSigueLiga.id_usuario == usuario_id,
        UsuarioSigueLiga.id_liga == liga_id
    ).first()

    if existente:
        raise ValueError("Ya sigues esta liga")

    # Crear seguimiento
    seguimiento = UsuarioSigueLiga(
        id_usuario=usuario_id,
        id_liga=liga_id
    )

    db.add(seguimiento)
    db.commit()
    db.refresh(seguimiento)

    return seguimiento


def dejar_de_seguir_liga(db: Session, usuario_id: int, liga_id: int):
    """
    Permite a un usuario dejar de seguir una liga.

    Elimina la relación de seguimiento entre el usuario y la liga.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        liga_id (int): ID de la liga a dejar de seguir

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si el usuario no sigue la liga
    """
    from app.models.usuario_sigue_liga import UsuarioSigueLiga

    # Buscar seguimiento
    seguimiento = db.query(UsuarioSigueLiga).filter(
        UsuarioSigueLiga.id_usuario == usuario_id,
        UsuarioSigueLiga.id_liga == liga_id
    ).first()

    if not seguimiento:
        raise ValueError("No sigues esta liga")

    db.delete(seguimiento)
    db.commit()

    return True


def obtener_ligas_seguidas(db: Session, usuario_id: int):
    """
    Obtiene las ligas que sigue un usuario.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario

    Returns:
        List[Liga]: Lista de ligas seguidas por el usuario
    """
    from app.models.usuario_sigue_liga import UsuarioSigueLiga
    from app.models.liga import Liga

    # Obtener IDs de ligas seguidas
    seguimientos = db.query(UsuarioSigueLiga).filter(
        UsuarioSigueLiga.id_usuario == usuario_id
    ).all()

    ids_ligas = [s.id_liga for s in seguimientos]

    # Obtener ligas
    ligas = db.query(Liga).filter(Liga.id_liga.in_(ids_ligas)).all()

    return ligas


def obtener_ligas_con_rol(db: Session, usuario_id: int):
    """
    Obtiene las ligas donde el usuario tiene un rol asignado.

    Realiza un join entre las tablas usuario_rol, ligas y roles para obtener
    las ligas junto con el rol del usuario en cada una.

    Args:
        db (Session): Sesion de base de datos SQLAlchemy
        usuario_id (int): ID del usuario

    Returns:
        List[dict]: Lista de diccionarios con datos de la liga y el rol del usuario.
                     Cada diccionario contiene:
                     - id_liga: ID de la liga
                     - nombre: Nombre de la liga
                     - temporada: Temporada de la liga
                     - activa: Si la liga esta activa
                     - rol: Nombre del rol del usuario en esta liga
    """
    from app.models.usuario_rol import UsuarioRol
    from app.models.liga import Liga
    from app.models.rol import Rol

    # Query con join para obtener liga + rol del usuario
    resultados = (
        db.query(Liga, Rol)
        .join(UsuarioRol, UsuarioRol.id_liga == Liga.id_liga)
        .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
        .filter(UsuarioRol.id_usuario == usuario_id)
        .all()
    )

    # Construir lista de respuestas con datos de liga y rol
    ligas_con_rol = []
    for liga, rol in resultados:
        ligas_con_rol.append({
            "id_liga": liga.id_liga,
            "nombre": liga.nombre,
            "temporada": liga.temporada,
            "activa": liga.activa,
            "rol": rol.nombre
        })

    return ligas_con_rol
