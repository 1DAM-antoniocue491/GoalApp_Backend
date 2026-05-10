"""
Servicios de lógica de negocio para Usuario.
Maneja operaciones CRUD de usuarios, autenticación, gestión de contraseñas
con hashing bcrypt, y asignación de roles.
"""
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
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
    Elimina un usuario del sistema junto con sus dependencias (jugador, tokens, etc.).

    Carga las relaciones del usuario para asegurar que cascade delete funcione correctamente.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario a eliminar

    Raises:
        ValueError: Si el usuario no existe
    """
    from sqlalchemy.orm import joinedload
    from app.models.jugador import Jugador
    from app.models.token_recuperacion import TokenRecuperacion

    # Cargar usuario con sus relaciones para cascade delete
    usuario = db.query(Usuario).options(
        joinedload(Usuario.jugador),
        joinedload(Usuario.usuario_roles)
    ).filter(Usuario.id_usuario == usuario_id).first()

    if not usuario:
        raise ValueError("Usuario no encontrado")

    # Eliminar dependencias explícitamente para asegurar cascade
    # Tokens de recuperación
    db.query(TokenRecuperacion).filter(
        TokenRecuperacion.id_usuario == usuario_id
    ).delete(synchronize_session=False)

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


def cambiar_rol_en_liga(db: Session, usuario_id: int, liga_id: int, nuevo_rol_id: int):
    """
    Cambia el rol de un usuario en una liga específica.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        liga_id (int): ID de la liga
        nuevo_rol_id (int): ID del nuevo rol a asignar

    Returns:
        UsuarioRol: La asignación actualizada

    Raises:
        ValueError: Si el usuario no tiene un rol asignado en esa liga, o si el nuevo rol no existe
    """
    from app.models.liga import Liga

    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise ValueError("Liga no encontrada")

    # Verificar que el nuevo rol existe
    nuevo_rol = db.query(Rol).filter(Rol.id_rol == nuevo_rol_id).first()
    if not nuevo_rol:
        raise ValueError("Rol no encontrado")

    # Buscar la asignación actual del usuario en la liga
    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise ValueError("El usuario no tiene un rol asignado en esta liga")

    # Actualizar el rol
    asignacion.id_rol = nuevo_rol_id
    db.commit()
    db.refresh(asignacion)

    return asignacion


def eliminar_asignacion_liga(db: Session, usuario_id: int, liga_id: int):
    """
    Elimina la asignación de un usuario en una liga específica.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        liga_id (int): ID de la liga

    Returns:
        bool: True si se eliminó correctamente

    Raises:
        ValueError: Si el usuario no tiene un rol asignado en esa liga
    """
    # Buscar la asignación
    asignacion = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise ValueError("El usuario no tiene un rol asignado en esta liga")

    db.delete(asignacion)
    db.commit()

    return True


def cambiar_estado_usuario_en_liga(db: Session, usuario_id: int, liga_id: int, activo: bool):
    """
    Cambia el estado (activo/inactivo) de un usuario en una liga específica.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        usuario_id (int): ID del usuario
        liga_id (int): ID de la liga
        activo (bool): Nuevo estado (True=activo, False=inactivo)

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario

    Raises:
        ValueError: Si el usuario no tiene un rol asignado en esa liga
    """
    from app.schemas.usuario import UsuarioLigaResponse

    # Buscar la asignación
    asignacion = db.query(UsuarioRol).options(
        joinedload(UsuarioRol.usuario),
        joinedload(UsuarioRol.rol)
    ).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if not asignacion:
        raise ValueError("El usuario no tiene un rol asignado en esta liga")

    # Save relationship data before commit (expires the instance)
    nombre_usuario = asignacion.usuario.nombre
    email = asignacion.usuario.email
    nombre_rol = asignacion.rol.nombre

    # Actualizar el estado
    asignacion.activo = 1 if activo else 0
    db.commit()

    # Return a serializable response (ORM relationships are expired after commit)
    return UsuarioLigaResponse(
        id_usuario_rol=asignacion.id_usuario_rol,
        id_usuario=asignacion.id_usuario,
        nombre_usuario=nombre_usuario,
        email=email,
        id_rol=asignacion.id_rol,
        nombre_rol=nombre_rol,
        activo=asignacion.activo
    )


def obtener_usuarios_con_roles(db: Session, liga_id: int):
    """
    Obtiene todos los usuarios con sus roles asignados en una liga específica.

    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        liga_id (int): ID de la liga

    Returns:
        list[dict]: Lista de diccionarios con información de usuario y rol

    Raises:
        ValueError: Si la liga no existe
    """
    from app.models.liga import Liga

    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise ValueError("Liga no encontrada")

    # Query con join para obtener usuario + rol + estado
    resultados = (
        db.query(Usuario, Rol, UsuarioRol)
        .join(UsuarioRol, UsuarioRol.id_usuario == Usuario.id_usuario)
        .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
        .filter(UsuarioRol.id_liga == liga_id)
        .all()
    )

    # Construir lista de respuestas
    usuarios_con_roles = []
    for usuario, rol, asignacion in resultados:
        usuarios_con_roles.append({
            "id_usuario_rol": asignacion.id_usuario_rol,
            "id_usuario": usuario.id_usuario,
            "nombre_usuario": usuario.nombre,
            "email": usuario.email,
            "id_rol": rol.id_rol,
            "nombre_rol": rol.nombre,
            "activo": asignacion.activo
        })

    return usuarios_con_roles

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
    fecha_expiracion = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

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
        TokenRecuperacion.fecha_expiracion > datetime.now(timezone.utc)
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
                     - equipos_total: Cantidad de equipos inscritos en la liga
    """
    from app.models.usuario_rol import UsuarioRol
    from app.models.liga import Liga
    from app.models.rol import Rol
    from app.models.equipo import Equipo
    from sqlalchemy import func

    # Query con join para obtener liga + rol del usuario
    resultados = (
        db.query(Liga, Rol)
        .join(UsuarioRol, UsuarioRol.id_liga == Liga.id_liga)
        .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
        .filter(UsuarioRol.id_usuario == usuario_id)
        .all()
    )

    if not resultados:
        return []

    # Extraer IDs de ligas para contar equipos en batch (evitar N+1)
    ids_ligas = [liga.id_liga for liga, _ in resultados]

    # Contar equipos de todas las ligas en una sola query con GROUP BY
    equipos_count_query = (
        db.query(Equipo.id_liga, func.count(Equipo.id_equipo).label('total'))
        .filter(Equipo.id_liga.in_(ids_ligas))
        .group_by(Equipo.id_liga)
        .all()
    )

    # Mapa: id_liga -> count de equipos
    equipos_map = {id_liga: total for id_liga, total in equipos_count_query}

    # Construir lista de respuestas con datos de liga y rol
    ligas_con_rol = []
    for liga, rol in resultados:
        ligas_con_rol.append({
            "id_liga": liga.id_liga,
            "nombre": liga.nombre,
            "temporada": liga.temporada,
            "activa": liga.activa,
            "rol": rol.nombre,
            "equipos_total": equipos_map.get(liga.id_liga, 0)
        })

    return ligas_con_rol


def obtener_usuarios_con_rol_en_liga(db: Session, liga_id: int, solo_activos: bool = False):
    """
    Obtiene todos los usuarios que tienen un rol asignado en una liga específica.

    Realiza un join entre las tablas usuario_rol, usuarios y roles para obtener
    los usuarios junto con sus roles en la liga especificada.

    Args:
        db (Session): Sesion de base de datos SQLAlchemy
        liga_id (int): ID de la liga
        solo_activos (bool): Si True, filtra solo usuarios con estado activo

    Returns:
        List[dict]: Lista de diccionarios con datos del usuario y su rol en la liga.
                     Cada diccionario contiene:
                     - id_usuario: ID del usuario
                     - nombre: Nombre del usuario
                     - email: Email del usuario
                     - id_rol: ID del rol
                     - rol: Nombre del rol (admin, entrenador, delegado, jugador, etc.)
                     - activo: bool
                     - id_equipo: ID del equipo (si aplica)
                     - nombre_equipo: Nombre del equipo (si aplica)
    """
    from sqlalchemy.orm import joinedload, selectinload
    from app.models.usuario_rol import UsuarioRol
    from app.models.usuario import Usuario
    from app.models.rol import Rol
    from app.models.jugador import Jugador
    from app.models.equipo import Equipo

    # Query con join para obtener usuario + rol + estado activo en la liga
    query = (
        db.query(Usuario, Rol, UsuarioRol.activo, UsuarioRol.id_usuario)
        .join(UsuarioRol, UsuarioRol.id_usuario == Usuario.id_usuario)
        .join(Rol, Rol.id_rol == UsuarioRol.id_rol)
        .filter(UsuarioRol.id_liga == liga_id)
    )

    # Filtrar solo activos si se solicita
    if solo_activos:
        query = query.filter(UsuarioRol.activo == True)

    resultados = query.all()

    if not resultados:
        return []

    # Extraer IDs de usuario para cargar datos relacionados en batch (evitar N+1)
    ids_usuarios = [id_usuario for _, _, _, id_usuario in resultados]

    # Cargar todos los jugadores de esta liga en una sola query (selectinload manual)
    jugadores = (
        db.query(Jugador)
        .join(Equipo, Jugador.id_equipo == Equipo.id_equipo)
        .filter(Jugador.id_usuario.in_(ids_usuarios), Equipo.id_liga == liga_id)
        .all()
    )
    # Mapa: id_usuario -> jugador
    jugadores_map = {j.id_usuario: j for j in jugadores}

    # Extraer IDs de equipo de los jugadores para cargar equipos en batch
    ids_equipos_jugadores = [j.id_equipo for j in jugadores if j.id_equipo]

    # Obtener IDs de equipos de entrenadores y delegados
    entrenadores_ids = [id_usuario for _, rol, _, id_usuario in resultados if rol.nombre == 'entrenador']
    delegados_ids = [id_usuario for _, rol, _, id_usuario in resultados if rol.nombre == 'delegado']

    # Cargar equipos de entrenadores
    equipos_entrenadores = (
        db.query(Equipo)
        .filter(Equipo.id_entrenador.in_(entrenadores_ids), Equipo.id_liga == liga_id)
        .all()
    )
    equipos_por_entrenador_map = {e.id_entrenador: e for e in equipos_entrenadores}

    # Cargar equipos de delegados
    equipos_delegados = (
        db.query(Equipo)
        .filter(Equipo.id_delegado.in_(delegados_ids), Equipo.id_liga == liga_id)
        .all()
    )
    equipos_por_delegado_map = {e.id_delegado: e for e in equipos_delegados}

    # Cargar todos los equipos de los jugadores en una sola query
    equipos_jugadores = (
        db.query(Equipo)
        .filter(Equipo.id_equipo.in_(ids_equipos_jugadores))
        .all()
    )
    equipos_map = {e.id_equipo: e for e in equipos_jugadores}

    # Construir lista de respuestas con datos de usuario y rol
    usuarios_con_rol = []
    for usuario, rol, activo, id_usuario in resultados:
        usuario_data = {
            "id_usuario": id_usuario,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "id_rol": rol.id_rol,
            "rol": rol.nombre,
            "activo": bool(activo),
            "id_equipo": None,
            "nombre_equipo": None,
            "estadio": None,
        }

        # Obtener equipo según el rol (usando mapas en lugar de queries individuales)
        if rol.nombre == 'jugador':
            jugador = jugadores_map.get(id_usuario)
            if jugador:
                usuario_data["id_equipo"] = jugador.id_equipo
                equipo = equipos_map.get(jugador.id_equipo)
                if equipo:
                    usuario_data["nombre_equipo"] = equipo.nombre
                    usuario_data["estadio"] = equipo.estadio
        elif rol.nombre == 'entrenador':
            equipo = equipos_por_entrenador_map.get(id_usuario)
            if equipo:
                usuario_data["id_equipo"] = equipo.id_equipo
                usuario_data["nombre_equipo"] = equipo.nombre
                usuario_data["estadio"] = equipo.estadio
        elif rol.nombre == 'delegado':
            equipo = equipos_por_delegado_map.get(id_usuario)
            if equipo:
                usuario_data["id_equipo"] = equipo.id_equipo
                usuario_data["nombre_equipo"] = equipo.nombre
                usuario_data["estadio"] = equipo.estadio

        usuarios_con_rol.append(usuario_data)

    return usuarios_con_rol


# ============================================================
# RELEVO DE ADMINISTRADOR
# ============================================================


def relevo_admin(db: Session, liga_id: int, admin_actual_id: int, nuevo_admin_id: int):
    """
    Realiza el relevo de administrador de una liga.
    El admin actual pasa a ser "viewer" (observador) y el nuevo usuario se convierte en admin.

    Args:
        db: Sesión de base de datos
        liga_id: ID de la liga
        admin_actual_id: ID del usuario que es admin actual
        nuevo_admin_id: ID del usuario que será el nuevo admin

    Raises:
        ValueError: Si algún usuario no existe, no tiene el rol esperado, o la liga no existe
    """
    from app.models.usuario import Usuario
    from app.models.rol import Rol
    from app.models.liga import Liga
    from app.models.usuario_rol import UsuarioRol

    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise ValueError(f"Liga con ID {liga_id} no encontrada")

    # Verificar que el admin actual tiene rol de admin
    admin_actual_rol = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == admin_actual_id,
        UsuarioRol.id_liga == liga_id
    ).join(Rol).filter(Rol.nombre == "admin").first()

    if not admin_actual_rol:
        raise ValueError("El usuario actual no tiene rol de administrador en esta liga")

    # Verificar que el nuevo admin existe
    nuevo_admin = db.query(Usuario).filter(Usuario.id_usuario == nuevo_admin_id).first()
    if not nuevo_admin:
        raise ValueError(f"Usuario con ID {nuevo_admin_id} no encontrado")

    # Obtener rol de viewer
    rol_viewer = db.query(Rol).filter(Rol.nombre == "viewer").first()
    if not rol_viewer:
        raise ValueError("Rol 'viewer' no encontrado en la base de datos")

    # Obtener rol de admin
    rol_admin = db.query(Rol).filter(Rol.nombre == "admin").first()
    if not rol_admin:
        raise ValueError("Rol 'admin' no encontrado en la base de datos")

    # Actualizar admin actual a viewer (en misma transacción)
    admin_actual_rol.id_rol = rol_viewer.id_rol
    admin_actual_rol.activo = 1  # Asegurar que sigue activo como viewer

    # Verificar si nuevo admin ya tiene algún rol en la liga
    nuevo_admin_rol = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == nuevo_admin_id,
        UsuarioRol.id_liga == liga_id
    ).first()

    if nuevo_admin_rol:
        # Actualizar rol existente a admin
        nuevo_admin_rol.id_rol = rol_admin.id_rol
        nuevo_admin_rol.activo = 1
    else:
        # Crear nuevo rol para el nuevo admin
        nuevo_admin_rol = UsuarioRol(
            id_usuario=nuevo_admin_id,
            id_rol=rol_admin.id_rol,
            id_liga=liga_id,
            activo=1
        )
        db.add(nuevo_admin_rol)

    db.commit()

    return True
