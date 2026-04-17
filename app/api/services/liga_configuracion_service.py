"""
Servicios de lógica de negocio para LigaConfiguracion.
Maneja la configuración específica de cada liga.
"""
from sqlalchemy.orm import Session
from app.models.liga_configuracion import LigaConfiguracion
from app.schemas.liga_configuracion import LigaConfiguracionCreate, LigaConfiguracionUpdate


def obtener_configuracion(db: Session, liga_id: int):
    return db.query(LigaConfiguracion).filter(LigaConfiguracion.id_liga == liga_id).first()


def crear_configuracion(db: Session, liga_id: int, datos: LigaConfiguracionCreate):
    existente = obtener_configuracion(db, liga_id)
    if existente:
        raise ValueError("La liga ya tiene configuración")

    configuracion = LigaConfiguracion(
        id_liga=liga_id,
        hora_partidos=datos.hora_partidos,
        min_equipos=datos.min_equipos,
        max_equipos=datos.max_equipos,
        min_convocados=datos.min_convocados,
        max_convocados=datos.max_convocados,
        min_plantilla=datos.min_plantilla,
        max_plantilla=datos.max_plantilla,
        min_jugadores_equipo=datos.min_jugadores_equipo,
        min_partidos_entre_equipos=datos.min_partidos_entre_equipos,
        minutos_partido=datos.minutos_partido,
        max_partidos=datos.max_partidos,
    )
    db.add(configuracion)
    db.commit()
    db.refresh(configuracion)
    return configuracion


def actualizar_configuracion(db: Session, liga_id: int, datos: LigaConfiguracionUpdate):
    configuracion = obtener_configuracion(db, liga_id)
    if not configuracion:
        raise ValueError("La liga no tiene configuración")

    update_fields = [
        'hora_partidos', 'min_equipos', 'max_equipos',
        'min_convocados', 'max_convocados',
        'min_plantilla', 'max_plantilla',
        'min_jugadores_equipo', 'min_partidos_entre_equipos',
        'minutos_partido', 'max_partidos',
    ]

    for field in update_fields:
        value = getattr(datos, field, None)
        if value is not None:
            setattr(configuracion, field, value)

    db.commit()
    db.refresh(configuracion)
    return configuracion


def crear_configuracion_por_defecto(db: Session, liga_id: int):
    configuracion = LigaConfiguracion(id_liga=liga_id)
    db.add(configuracion)
    db.commit()
    db.refresh(configuracion)
    return configuracion