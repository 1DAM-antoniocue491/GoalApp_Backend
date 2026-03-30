"""
Servicios de lógica de negocio para Formación.
Maneja formaciones tácticas (ej: 4-4-2, 4-3-3) y sus posiciones específicas.
Permite crear y gestionar esquemas tácticos para equipos.
"""
from sqlalchemy.orm import Session
from app.models.formacion import Formacion
from app.models.posicion_formacion import PosicionFormacion
from app.schemas.formacion import FormacionCreate, FormacionUpdate, FormacionResponse


def crear_formacion(db: Session, datos: FormacionCreate):
    """
    Crea una nueva formación táctica.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (FormacionCreate): Datos de la formación (nombre como "4-4-2")
    
    Returns:
        Formacion: Objeto Formacion creado con su ID asignado
    """
    formacion = Formacion(nombre=datos.nombre)
    db.add(formacion)
    db.commit()
    db.refresh(formacion)
    return formacion


def obtener_formaciones(db: Session):
    """
    Obtiene todas las formaciones tácticas disponibles.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
    
    Returns:
        list[Formacion]: Lista con todas las formaciones registradas
    """
    return db.query(Formacion).all()

'''
def crear_posicion(db: Session, datos: PosicionCreate):
    """
    Crea una posición específica dentro de una formación.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        datos (PosicionCreate): Datos de la posición (formación asociada y nombre)
    
    Returns:
        PosicionFormacion: Objeto PosicionFormacion creado con su ID asignado
    """
    posicion = PosicionFormacion(
        id_formacion=datos.id_formacion,
        nombre=datos.nombre
    )
    db.add(posicion)
    db.commit()
    db.refresh(posicion)
    return posicion
'''

def obtener_posiciones(db: Session, formacion_id: int):
    """
    Obtiene todas las posiciones de una formación específica.
    
    Args:
        db (Session): Sesión de base de datos SQLAlchemy
        formacion_id (int): ID de la formación
    
    Returns:
        list[PosicionFormacion]: Lista de posiciones de la formación
    """
    return db.query(PosicionFormacion).filter(PosicionFormacion.id_formacion == formacion_id).all()
