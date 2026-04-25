# app/api/routers/equipos.py
"""
Router de Equipos - Gestión de equipos de fútbol.
Endpoints para crear, listar, actualizar y eliminar equipos.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role, get_current_user
from app.models.usuario import Usuario
from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoResponse, EquipoRendimientoResponse
from app.api.services.equipo_service import (
    crear_equipo,
    obtener_equipos,
    obtener_equipo_por_id,
    actualizar_equipo,
    eliminar_equipo,
    obtener_equipos_con_rendimiento,
    obtener_detalle_equipo,
    obtener_proximos_partidos,
    obtener_ultimos_partidos,
    obtener_goleadores_equipo,
    obtener_plantilla_equipo,
    obtener_staff_equipo,
    obtener_miembros_equipo,
    asignar_delegado,
    actualizar_estado_miembro,
    eliminar_miembro_equipo
)

# Configuración del router
router = APIRouter(
    prefix="/equipos",  # Base path: /api/v1/equipos
    tags=["Equipos"]  # Agrupación en documentación
)

@router.post("/", response_model=EquipoResponse, dependencies=[Depends(require_role("admin"))])
def crear_equipo_router(
    equipo: EquipoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear un nuevo equipo.

    Registra un nuevo equipo en el sistema con su información básica.

    Parámetros:
        - equipo (EquipoCreate): Datos del equipo a crear (nombre, escudo, ciudad, etc.)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado (inyectado desde JWT)

    Returns:
        EquipoResponse: Información del equipo creado con su ID asignado

    Requiere autenticación: Sí
    Roles permitidos: Admin

    Nota:
        Si no se especifica id_entrenador o id_delegado, se usa el ID del usuario
        que crea el equipo (requiere autenticación).
    """
    return crear_equipo(db, equipo, current_user.id_usuario)

@router.get("/", response_model=list[EquipoResponse])
def listar_equipos(liga_id: int = None, db: Session = Depends(get_db)):
    """
    Listar todos los equipos, opcionalmente filtrados por liga.

    Obtiene la lista completa de equipos registrados en el sistema.
    Si se proporciona liga_id, solo devuelve los equipos de esa liga.

    Parámetros:
        - liga_id (int, optional): ID de la liga para filtrar (query parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[EquipoResponse]: Lista de equipos (filtrados por liga si se proporciona)

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_equipos(db, liga_id)

@router.get("/{equipo_id}", response_model=EquipoResponse)
def obtener_equipo_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener un equipo por su ID.

    Devuelve la información detallada de un equipo específico.

    Parámetros:
        - equipo_id (int): ID único del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        EquipoResponse: Información completa del equipo

    Requiere autenticación: No
    Roles permitidos: Público

    Raises:
        HTTPException 404: Si el equipo no existe
    """
    equipo = obtener_equipo_por_id(db, equipo_id)
    # Validar que el equipo exista
    if not equipo:
        raise HTTPException(404, "Equipo no encontrado")
    return equipo


@router.get("/ligas/{liga_id}/rendimiento", response_model=list[EquipoRendimientoResponse])
def listar_equipos_rendimiento(liga_id: int, db: Session = Depends(get_db)):
    """
    Listar todos los equipos de una liga con sus estadísticas de rendimiento.

    Obtiene la lista de equipos de una liga específica junto con sus estadísticas
    de victorias, empates y derrotas calculadas a partir de los partidos finalizados.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[EquipoRendimientoResponse]: Lista de equipos con sus estadísticas,
                                          ordenada por porcentaje de victorias descendente

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_equipos_con_rendimiento(db, liga_id)

@router.put("/{equipo_id}", response_model=EquipoResponse, dependencies=[Depends(require_role("admin"))])
def actualizar_equipo_router(equipo_id: int, datos: EquipoUpdate, db: Session = Depends(get_db)):
    """
    Actualizar información de un equipo.
    
    Modifica los datos de un equipo existente. Solo se actualizan los campos
    proporcionados en el body de la petición.
    
    Parámetros:
        - equipo_id (int): ID del equipo a actualizar (path parameter)
        - datos (EquipoUpdate): Campos del equipo a modificar
        - db (Session): Sesión de base de datos
    
    Returns:
        EquipoResponse: Información actualizada del equipo
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return actualizar_equipo(db, equipo_id, datos)

@router.delete("/{equipo_id}", dependencies=[Depends(require_role("admin"))])
def eliminar_equipo_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un equipo.

    Elimina un equipo del sistema. Esta acción puede afectar registros relacionados
    como jugadores, partidos y formaciones.

    Parámetros:
        - equipo_id (int): ID del equipo a eliminar (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    eliminar_equipo(db, equipo_id)
    return {"mensaje": "Equipo eliminado correctamente"}


@router.get("/{equipo_id}/detalle")
def obtener_detalle_equipo_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener detalle completo de un equipo con estadísticas.

    Devuelve información extendida del equipo incluyendo posición en liga,
    puntos, tasa de victoria, goles a favor y en contra.

    Parámetros:
        - equipo_id (int): ID único del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        dict: Información completa del equipo con estadísticas

    Requiere autenticación: No
    Roles permitidos: Público
    """
    equipo = obtener_equipo_por_id(db, equipo_id)
    if not equipo:
        raise HTTPException(404, "Equipo no encontrado")

    detalle = obtener_detalle_equipo(db, equipo_id, equipo.id_liga)
    if not detalle:
        raise HTTPException(404, "Equipo no encontrado")

    return detalle


@router.get("/{equipo_id}/partidos/proximos")
def obtener_proximos_partidos_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener próximos partidos de un equipo.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        list: Lista de próximos partidos

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_proximos_partidos(db, equipo_id)


@router.get("/{equipo_id}/partidos/ultimos")
def obtener_ultimos_partidos_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener últimos partidos finalizados de un equipo.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        list: Lista de últimos partidos con resultado (W/D/L)

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_ultimos_partidos(db, equipo_id)


@router.get("/{equipo_id}/goleadores")
def obtener_goleadores_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener máximos goleadores de un equipo.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        list: Lista de jugadores ordenados por goles

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_goleadores_equipo(db, equipo_id)


@router.get("/{equipo_id}/plantilla")
def obtener_plantilla_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener plantilla completa de un equipo.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        list: Lista de jugadores con sus estadísticas

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_plantilla_equipo(db, equipo_id)


@router.get("/{equipo_id}/staff")
def obtener_staff_router(equipo_id: int, db: Session = Depends(get_db)):
    """
    Obtener staff de un equipo (entrenador y capitán).

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        dict: Información del entrenador y capitán

    Requiere autenticación: No
    Roles permitidos: Público
    """
    staff = obtener_staff_equipo(db, equipo_id)
    if not staff:
        raise HTTPException(404, "Equipo no encontrado")
    return staff


@router.get("/usuario/mi-equipo")
def obtener_mi_equipo(
    liga_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener el equipo del usuario actual en una liga específica.

    Parámetros:
        - liga_id (int): ID de la liga (query parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Información del equipo con id_equipo, nombre, escudo, etc.

    Requiere autenticación: Sí
    Roles permitidos: Todos los autenticados

    Raises:
        HTTPException 404: Si el usuario no tiene equipo en esa liga
    """
    from app.models.equipo import Equipo
    from app.models.jugador import Jugador

    # Buscar si el usuario es jugador en algún equipo de la liga
    jugador = db.query(Jugador).join(
        Equipo, Jugador.id_equipo == Equipo.id_equipo
    ).filter(
        Jugador.id_usuario == current_user.id_usuario,
        Equipo.id_liga == liga_id
    ).first()

    if jugador:
        equipo = db.query(Equipo).filter(Equipo.id_equipo == jugador.id_equipo).first()
        return {
            "id_equipo": equipo.id_equipo,
            "nombre": equipo.nombre,
            "escudo": equipo.escudo,
            "colores": equipo.colores,
            "id_liga": equipo.id_liga,
            "id_entrenador": equipo.id_entrenador,
            "id_delegado": equipo.id_delegado,
        }

    # Buscar si el usuario es entrenador o delegado
    equipo = db.query(Equipo).filter(
        ((Equipo.id_entrenador == current_user.id_usuario) |
         (Equipo.id_delegado == current_user.id_usuario)) &
        (Equipo.id_liga == liga_id)
    ).first()

    if equipo:
        return {
            "id_equipo": equipo.id_equipo,
            "nombre": equipo.nombre,
            "escudo": equipo.escudo,
            "colores": equipo.colores,
            "id_liga": equipo.id_liga,
            "id_entrenador": equipo.id_entrenador,
            "id_delegado": equipo.id_delegado,
        }

    raise HTTPException(404, "Usuario no tiene equipo en esta liga")


@router.get("/{equipo_id}/miembros")
def obtener_miembros_equipo_router(
    equipo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener todos los miembros de un equipo (jugadores + delegado).

    Solo el entrenador del equipo puede acceder a esta información.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        list: Lista de miembros con su información (nombre, email, tipo, estado)

    Requiere autenticación: Sí
    Roles permitidos: Entrenador del equipo

    Raises:
        HTTPException 403: Si el usuario no es el entrenador del equipo
        HTTPException 404: Si el equipo no existe
    """
    from app.models.equipo import Equipo

    equipo = db.query(Equipo).filter(Equipo.id_equipo == equipo_id).first()
    if not equipo:
        raise HTTPException(404, "Equipo no encontrado")

    # Verificar que el usuario es el entrenador
    if equipo.id_entrenador != current_user.id_usuario:
        raise HTTPException(403, "Solo el entrenador puede ver los miembros de su equipo")

    return obtener_miembros_equipo(db, equipo_id)


@router.put("/{equipo_id}/delegado")
def asignar_delegado_router(
    equipo_id: int,
    datos: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Asignar o cambiar el delegado de un equipo.

    Solo el entrenador del equipo puede realizar esta acción.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - datos (dict): {"id_usuario": int} - ID del usuario a asignar como delegado
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Información del delegado asignado

    Requiere autenticación: Sí
    Roles permitidos: Entrenador del equipo

    Raises:
        HTTPException 403: Si el usuario no es el entrenador
        HTTPException 404: Si el equipo o usuario no existen
    """
    try:
        id_usuario = datos.get("id_usuario")
        if not id_usuario:
            raise HTTPException(400, "id_usuario es requerido")
        return asignar_delegado(db, equipo_id, id_usuario, current_user.id_usuario)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/{equipo_id}/miembros/{usuario_id}/estado")
def actualizar_estado_miembro_router(
    equipo_id: int,
    usuario_id: int,
    datos: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar el estado (activo/inactivo) de un miembro del equipo.

    Solo el entrenador puede realizar esta acción.
    No se puede desactivar al propio entrenador.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - usuario_id (int): ID del usuario miembro (path parameter)
        - datos (dict): {"activo": bool} - Nuevo estado
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Información del miembro actualizado

    Requiere autenticación: Sí
    Roles permitidos: Entrenador del equipo

    Raises:
        HTTPException 403: Si el usuario no es el entrenador
        HTTPException 404: Si el equipo o miembro no existen
    """
    try:
        activo = datos.get("activo", True)
        return actualizar_estado_miembro(db, equipo_id, usuario_id, activo, current_user.id_usuario)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/{equipo_id}/miembros/{usuario_id}")
def eliminar_miembro_equipo_router(
    equipo_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Eliminar un miembro del equipo (jugador o delegado).

    Solo el entrenador puede realizar esta acción.
    No se puede eliminar al propio entrenador.

    Parámetros:
        - equipo_id (int): ID del equipo (path parameter)
        - usuario_id (int): ID del usuario miembro (path parameter)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    Roles permitidos: Entrenador del equipo

    Raises:
        HTTPException 403: Si el usuario no es el entrenador
        HTTPException 404: Si el equipo o miembro no existen
    """
    try:
        return eliminar_miembro_equipo(db, equipo_id, usuario_id, current_user.id_usuario)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
