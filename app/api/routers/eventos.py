# app/api/routers/eventos.py
"""
Router de Eventos - Gestión de eventos de partido.
Endpoints para registrar y consultar eventos ocurridos durante los partidos
(goles, tarjetas, sustituciones, etc.).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.schemas.eventos import EventoPartidoBase, EventoPartidoCreate, EventoPartidoUpdate, EventoPartidoResponse
from app.api.services.evento_service import crear_evento, obtener_eventos_por_partido
from app.models.usuario import Usuario

# Configuración del router
router = APIRouter(
    prefix="/eventos",  # Base path: /api/v1/eventos
    tags=["Eventos"]  # Agrupación en documentación
)

@router.post("/", response_model=EventoPartidoResponse)
def crear_evento_router(
    evento: EventoPartidoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registrar un nuevo evento en un partido.

    Crea un evento durante el transcurso de un partido (gol, tarjeta amarilla,
    tarjeta roja, sustitución, etc.).

    SOLO el delegado del equipo LOCAL puede crear eventos del partido.

    Parámetros:
        - evento (EventoPartidoCreate): Datos del evento (partido_id, jugador_id, minuto, tipo)
        - db (Session): Sesión de base de datos
        - current_user (Usuario): Usuario autenticado

    Returns:
        EventoPartidoResponse: Información del evento creado

    Requiere autenticación: Sí
    Roles permitidos: Delegate (solo del equipo local)

    Raises:
        HTTPException 403: Si el usuario no es delegado del equipo local
        HTTPException 400: Si el partido o jugador no existen
    """
    try:
        return crear_evento(db, evento, current_user.id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/partido/{partido_id}", response_model=list[EventoPartidoResponse])
def listar_eventos_partido(partido_id: int, db: Session = Depends(get_db)):
    """
    Listar todos los eventos de un partido específico.

    Obtiene la cronología completa de eventos ocurridos durante un partido,
    ordenados por minuto de juego.

    Parámetros:
        - partido_id (int): ID del partido (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[EventoPartidoResponse]: Lista de eventos del partido

    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_eventos_por_partido(db, partido_id)
