# app/api/routers/ligas.py
"""
Router de Ligas - Gestión de ligas y competiciones.
Endpoints para crear, listar, actualizar y eliminar ligas de fútbol.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role, get_current_user
from app.schemas.liga import LigaCreate, LigaUpdate, LigaResponse
from app.schemas.clasificacion import ClasificacionItem
from app.api.services.liga_service import (
    crear_liga,
    obtener_ligas,
    obtener_liga_por_id,
    actualizar_liga,
    eliminar_liga,
    obtener_clasificacion,
    reactivar_liga,
    desactivar_liga,
    obtener_usuarios_liga,
    actualizar_rol_usuario,
    actualizar_estado_usuario,
    eliminar_usuario_liga
)
from app.schemas.gestion_usuarios import UsuarioRolUpdate, UsuarioEstadoUpdate, UsuarioLigaResponse
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.usuario_rol import UsuarioRol
from app.models.equipo import Equipo
from app.models.jugador import Jugador
from sqlalchemy import func

# Configuración del router
router = APIRouter(
    prefix="/ligas",  # Base path: /api/v1/ligas
    tags=["Ligas"]  # Agrupación en documentación
)

@router.post("/", response_model=LigaResponse)
def crear_liga_router(liga: LigaCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Crear una nueva liga.

    Registra una nueva liga o competición en el sistema con su información básica.
    El usuario creador es automáticamente asignado como admin de la liga.

    Parámetros:
        - liga (LigaCreate): Datos de la liga (nombre, país, temporada, etc.)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (se obtiene del token JWT)

    Returns:
        LigaResponse: Información de la liga creada con su ID asignado

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_liga(db, liga, id_usuario_creador=current_user.id_usuario)

@router.get("/", response_model=list[LigaResponse])
def listar_ligas(db: Session = Depends(get_db)):
    """
    Listar todas las ligas.
    
    Obtiene la lista completa de ligas registradas en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[LigaResponse]: Lista de todas las ligas
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_ligas(db)

@router.get("/{liga_id}", response_model=LigaResponse)
def obtener_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener una liga por su ID.
    
    Devuelve la información detallada de una liga específica.
    
    Parámetros:
        - liga_id (int): ID único de la liga (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        LigaResponse: Información completa de la liga
    
    Requiere autenticación: No
    Roles permitidos: Público
    
    Raises:
        HTTPException 404: Si la liga no existe
    """
    liga = obtener_liga_por_id(db, liga_id)
    # Validar que la liga exista
    if not liga:
        raise HTTPException(404, "Liga no encontrada")
    return liga

@router.put("/{liga_id}", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_liga_router(liga_id: int, datos: LigaUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de una liga.
    
    Modifica los datos de una liga existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - liga_id (int): ID de la liga a actualizar (path parameter)
        - datos (LigaUpdate): Campos de la liga a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        LigaResponse: Información actualizada de la liga
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_liga(db, liga_id, datos)

@router.delete("/{liga_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Eliminar una liga.
    
    Elimina una liga del sistema. Esta acción puede afectar registros relacionados
    como partidos y equipos asociados a la liga.
    
    Parámetros:
        - liga_id (int): ID de la liga a eliminar (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        dict: Mensaje de confirmación
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_liga(db, liga_id)
    return {"mensaje": "Liga eliminada"}

@router.get("/{liga_id}/clasificacion", response_model=list[ClasificacionItem])
def obtener_clasificacion_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener la clasificación de una liga.

    Calcula y devuelve la tabla de clasificación ordenada por:
    1. Puntos (descendente)
    2. Diferencia de goles (descendente)
    3. Goles a favor (descendente)

    Solo considera partidos con estado "finalizado".

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[ClasificacionItem]: Lista de equipos con sus estadísticas ordenados por posición

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 404: Si la liga no existe
    """
    try:
        return obtener_clasificacion(db, liga_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.put("/{liga_id}/reactivar", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def reactivar_liga_router(liga_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Reactivar una liga inactiva.

    Cambia el estado de una liga de inactiva a activa. Solo los administradores
    de la liga pueden realizar esta acción.

    Parámetros:
        - liga_id (int): ID de la liga a reactivar (path parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (se obtiene del token JWT)

    Returns:
        LigaResponse: Información de la liga reactivada

    Requiere autenticación: Sí
    Roles permitidos: Admin de la liga

    Raises:
        HTTPException 404: Si la liga no existe
        HTTPException 400: Si la liga ya está activa
        HTTPException 403: Si el usuario no es admin de la liga
    """
    try:
        return reactivar_liga(db, liga_id, id_usuario=current_user.id_usuario)
    except ValueError as e:
        if "no encontrada" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))

@router.put("/{liga_id}/desactivar", response_model=LigaResponse, dependencies=[Depends(require_role("admin"))])
def desactivar_liga_router(liga_id: int, db: Session = Depends(get_db)):
    """
    Desactivar una liga activa.

    Cambia el estado de una liga de activa a inactiva. Solo los administradores
    pueden realizar esta acción. Una liga inactiva no permite crear nuevos partidos
    ni modificar datos.

    Parámetros:
        - liga_id (int): ID de la liga a desactivar (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        LigaResponse: Información de la liga desactivada

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga no existe
        HTTPException 400: Si la liga ya está inactiva
    """
    try:
        return desactivar_liga(db, liga_id)
    except ValueError as e:
        if "no encontrada" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.get("/{liga_id}/usuarios", response_model=list[UsuarioLigaResponse])
def listar_usuarios_liga(liga_id: int, db: Session = Depends(get_db)):
    """
    Listar todos los usuarios de una liga con sus roles y estados.

    Obtiene la lista completa de usuarios que pertenecen a una liga,
    incluyendo su rol actual y estado (activo/pendiente).

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[UsuarioLigaResponse]: Lista de usuarios con su información de rol

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_usuarios_liga(db, liga_id)


@router.put("/{liga_id}/usuarios/{usuario_id}/rol", response_model=UsuarioLigaResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_rol_usuario_router(
    liga_id: int,
    usuario_id: int,
    datos: UsuarioRolUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar el rol de un usuario en una liga.

    Permite cambiar el rol de un usuario dentro de una liga específica.
    Por ejemplo, cambiar de 'observador' a 'entrenador'.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - usuario_id (int): ID del usuario a actualizar (path parameter)
        - datos (UsuarioRolUpdate): Datos con el nuevo rol
        - db (Session): Sesión de base de datos

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga, usuario o rol no existen
        HTTPException 400: Si el usuario no pertenece a la liga o no tiene equipo (para rol entrenador)
    """
    try:
        return actualizar_rol_usuario(db, liga_id, usuario_id, datos)
    except ValueError as e:
        if "no encontrada" in str(e) or "no encontrado" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.put("/{liga_id}/usuarios/{usuario_id}/estado", response_model=UsuarioLigaResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_estado_usuario_router(
    liga_id: int,
    usuario_id: int,
    datos: UsuarioEstadoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar el estado de un usuario en una liga.

    Permite activar o desactivar (marcar como pendiente) un usuario en una liga.
    Útil para gestionar el estado de miembros sin eliminarlos permanentemente.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - usuario_id (int): ID del usuario a actualizar (path parameter)
        - datos (UsuarioEstadoUpdate): Datos con el nuevo estado (activo=True/False)
        - db (Session): Sesión de base de datos

    Returns:
        UsuarioLigaResponse: Información actualizada del usuario

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga o usuario no existen
        HTTPException 400: Si el usuario no pertenece a la liga
    """
    try:
        return actualizar_estado_usuario(db, liga_id, usuario_id, datos)
    except ValueError as e:
        if "no encontrada" in str(e) or "no encontrado" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.delete("/{liga_id}/usuarios/{usuario_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_usuario_liga_router(
    liga_id: int,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar un usuario de una liga.

    Elimina permanentemente la asignación de un usuario a una liga.
    Esta acción no se puede deshacer.

    Validaciones:
    - No se puede eliminar al único administrador de la liga
    - El usuario debe pertenecer a la liga

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - usuario_id (int): ID del usuario a eliminar (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Raises:
        HTTPException 404: Si la liga o usuario no existen
        HTTPException 400: Si el usuario no pertenece a la liga o es el único admin
    """
    try:
        return eliminar_usuario_liga(db, liga_id, usuario_id)
    except ValueError as e:
        if "no encontrada" in str(e) or "no encontrado" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))
