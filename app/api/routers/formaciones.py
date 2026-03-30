# app/api/routers/formaciones.py
"""
Router de Formaciones - Gestión de formaciones tácticas de equipos.
Endpoints para crear formaciones, definir posiciones y consultar esquemas tácticos.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_role
from app.schemas.formacion import (
    FormacionCreate, FormacionResponse, FormacionUpdate
)
from app.api.services.formacion_service import (
    crear_formacion,
    obtener_formaciones,
    # crear_posicion,
    obtener_posiciones
)

# Configuración del router
router = APIRouter(
    prefix="/formaciones",  # Base path: /api/v1/formaciones
    tags=["Formaciones"]  # Agrupación en documentación
)

@router.post("/", response_model=FormacionResponse, dependencies=[Depends(require_role("admin"))])
def crear_formacion_router(formacion: FormacionCreate, db: Session = Depends(get_db)):
    """
    Crear una nueva formación táctica.
    
    Define un esquema táctico para un equipo en un partido específico
    (ej: 4-4-2, 4-3-3, 3-5-2).
    
    Parámetros:
        - formacion (FormacionCreate): Datos de la formación (partido_id, equipo_id, esquema)
        - db (Session): Sesión de base de datos
    
    Returns:
        FormacionResponse: Información de la formación creada
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_formacion(db, formacion)

@router.get("/", response_model=list[FormacionResponse])
def listar_formaciones(db: Session = Depends(get_db)):
    """
    Listar todas las formaciones registradas.
    
    Obtiene todas las formaciones tácticas definidas en el sistema.
    
    Parámetros:
        - db (Session): Sesión de base de datos
    
    Returns:
        List[FormacionResponse]: Lista de formaciones
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_formaciones(db)
'''
@router.post("/posiciones", response_model=PosicionResponse, dependencies=[Depends(require_role("admin"))])
def crear_posicion_router(posicion: PosicionCreate, db: Session = Depends(get_db)):
    """
    Asignar un jugador a una posición en una formación.
    
    Define la posición específica de un jugador dentro de una formación táctica,
    incluyendo sus coordenadas en el campo.
    
    Parámetros:
        - posicion (PosicionCreate): Datos de la posición (formacion_id, jugador_id, coordenadas)
        - db (Session): Sesión de base de datos
    
    Returns:
        PosicionResponse: Información de la posición creada
    
    Requiere autenticación: Sí
    Roles permitidos: Admin
    """
    return crear_posicion(db, posicion)

@router.get("/posiciones/{formacion_id}", response_model=list[PosicionResponse])
def listar_posiciones(formacion_id: int, db: Session = Depends(get_db)):
    """
    Listar todas las posiciones de una formación específica.
    
    Obtiene el detalle completo de los jugadores y sus posiciones dentro
    de una formación táctica.
    
    Parámetros:
        - formacion_id (int): ID de la formación (path parameter)
        - db (Session): Sesión de base de datos
    
    Returns:
        List[PosicionResponse]: Lista de posiciones con jugadores asignados
    
    Requiere autenticación: No
    Roles permitidos: Público
    """
    return obtener_posiciones(db, formacion_id)
'''