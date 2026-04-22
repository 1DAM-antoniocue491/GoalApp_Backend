# app/api/routers/estadisticas.py
"""
Router de Estadísticas - Estadísticas de fútbol de la liga.
Endpoints para obtener estadísticas generales, goleadores, MVP y más.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional

from app.api.dependencies import get_db
from app.models.liga import Liga
from app.models.partido import Partido
from app.models.evento_partido import EventoPartido
from app.models.jugador import Jugador
from app.models.usuario import Usuario
from app.models.equipo import Equipo
from app.schemas.estadisticas import (
    SeasonStatsResponse,
    TopScorerResponse,
    MatchdayMVPResponse,
    TeamGoalsStatsResponse,
)

# Constantes para tipos de eventos
TIPO_GOL = "GOL"
TIPO_AMARILLA = "TARJETA_AMARILLA"
TIPO_ROJA = "TARJETA_ROJA"
TIPO_ASISTENCIA = "ASISTENCIA"

router = APIRouter(
    prefix="/estadisticas",
    tags=["Estadísticas"]
)


@router.get("/liga/{liga_id}/temporada", response_model=SeasonStatsResponse)
def obtener_estadisticas_temporada(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener estadísticas generales de la temporada.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        SeasonStatsResponse: Estadísticas generales de la temporada

    Requiere autenticación: No
    Roles permitidos: Público
    """
    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    # Obtener IDs de equipos de la liga
    equipos_ids = db.query(Equipo.id_equipo).filter(Equipo.id_liga == liga_id).all()
    equipos_ids = [e[0] for e in equipos_ids]

    if not equipos_ids:
        return SeasonStatsResponse(
            total_partidos=0,
            total_goles=0,
            promedio_goles_por_partido=0,
            total_amarillas=0,
            total_rojas=0,
            total_asistencias=0,
            equipos_participantes=0,
            jugadores_registrados=0,
        )

    # Total de partidos finalizados
    total_partidos = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado == 'FINALIZADO'
    ).count()

    # Total de goles (eventos de tipo GOL)
    total_goles = db.query(EventoPartido).filter(
        EventoPartido.tipo_evento == TIPO_GOL,
        EventoPartido.id_partido.in_(
            db.query(Partido.id_partido).filter(Partido.id_liga == liga_id)
        )
    ).count()

    # Total de tarjetas amarillas
    total_amarillas = db.query(EventoPartido).filter(
        EventoPartido.tipo_evento == TIPO_AMARILLA,
        EventoPartido.id_partido.in_(
            db.query(Partido.id_partido).filter(Partido.id_liga == liga_id)
        )
    ).count()

    # Total de tarjetas rojas
    total_rojas = db.query(EventoPartido).filter(
        EventoPartido.tipo_evento == TIPO_ROJA,
        EventoPartido.id_partido.in_(
            db.query(Partido.id_partido).filter(Partido.id_liga == liga_id)
        )
    ).count()

    # Total de asistencias
    total_asistencias = db.query(EventoPartido).filter(
        EventoPartido.tipo_evento == TIPO_ASISTENCIA,
        EventoPartido.id_partido.in_(
            db.query(Partido.id_partido).filter(Partido.id_liga == liga_id)
        )
    ).count()

    # Equipos participantes
    equipos_participantes = len(equipos_ids)

    # Jugadores registrados (de equipos de la liga)
    jugadores_registrados = db.query(Jugador).filter(
        Jugador.id_equipo.in_(equipos_ids),
        Jugador.activo == True
    ).count()

    # Promedio de goles por partido
    promedio_goles = round(total_goles / total_partidos, 2) if total_partidos > 0 else 0

    return SeasonStatsResponse(
        total_partidos=total_partidos,
        total_goles=total_goles,
        promedio_goles_por_partido=promedio_goles,
        total_amarillas=total_amarillas,
        total_rojas=total_rojas,
        total_asistencias=total_asistencias,
        equipos_participantes=equipos_participantes,
        jugadores_registrados=jugadores_registrados,
    )


@router.get("/liga/{liga_id}/goleadores", response_model=List[TopScorerResponse])
def obtener_goleadores_liga(
    liga_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Obtener los máximos goleadores de la liga.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - limit (int): Cantidad de goleadores a devolver (query parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[TopScorerResponse]: Lista de goleadores ordenados por goles

    Requiere autenticación: No
    Roles permitidos: Público
    """
    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    # Obtener IDs de equipos de la liga
    equipos_ids = db.query(Equipo.id_equipo).filter(Equipo.id_liga == liga_id).all()
    equipos_ids = [e[0] for e in equipos_ids]

    if not equipos_ids:
        return []

    # Subquery para contar goles por jugador
    goles_subquery = db.query(
        EventoPartido.id_jugador,
        func.count(EventoPartido.id_evento).label('goles')
    ).filter(
        EventoPartido.tipo_evento == TIPO_GOL,
        EventoPartido.id_partido.in_(
            db.query(Partido.id_partido).filter(Partido.id_liga == liga_id)
        )
    ).group_by(EventoPartido.id_jugador).subquery()

    # Subquery para contar partidos jugados por jugador (partidos donde el jugador marcó gol)
    partidos_subquery = db.query(
        EventoPartido.id_jugador,
        func.count(func.distinct(EventoPartido.id_partido)).label('partidos')
    ).filter(
        EventoPartido.id_partido.in_(
            db.query(Partido.id_partido).filter(Partido.id_liga == liga_id)
        )
    ).group_by(EventoPartido.id_jugador).subquery()

    # Consulta principal
    resultados = db.query(
        Jugador,
        Usuario.nombre,
        Equipo.nombre.label('nombre_equipo'),
        Equipo.escudo.label('escudo_equipo'),
        goles_subquery.c.goles,
        partidos_subquery.c.partidos,
    ).join(
        Usuario, Jugador.id_usuario == Usuario.id_usuario
    ).join(
        Equipo, Jugador.id_equipo == Equipo.id_equipo
    ).join(
        goles_subquery, Jugador.id_jugador == goles_subquery.c.id_jugador
    ).join(
        partidos_subquery, Jugador.id_jugador == partidos_subquery.c.id_jugador, isouter=True
    ).filter(
        Jugador.id_equipo.in_(equipos_ids)
    ).order_by(
        goles_subquery.c.goles.desc()
    ).limit(limit).all()

    goleadores = []
    for jugador, nombre, nombre_equipo, escudo, goles, partidos in resultados:
        partidos_jugados = partidos if partidos else 0
        promedio = round(goles / partidos_jugados, 2) if partidos_jugados > 0 else 0
        goleadores.append(
            TopScorerResponse(
                id_jugador=jugador.id_jugador,
                id_usuario=jugador.id_usuario,
                id_equipo=jugador.id_equipo,
                nombre=nombre,
                nombre_equipo=nombre_equipo,
                escudo_equipo=escudo,
                goles=goles,
                partidos_jugados=partidos_jugados,
                promedio_goles=promedio,
            )
        )

    return goleadores


@router.get("/liga/{liga_id}/mvp", response_model=Optional[MatchdayMVPResponse])
def obtener_mvp_jornada(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener el MVP de la última jornada.

    NOTA: Esta es una implementación simplificada. En una versión completa,
    se debería calcular el rating basado en estadísticas de cada partido.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        Optional[MatchdayMVPResponse]: MVP de la jornada o null si no hay

    Requiere autenticación: No
    Roles permitidos: Público
    """
    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    # Obtener el partido más reciente finalizado
    partido_recente = db.query(Partido).filter(
        Partido.id_liga == liga_id,
        Partido.estado == 'FINALIZADO'
    ).order_by(Partido.fecha.desc()).first()

    if not partido_recente:
        return None

    # Obtener el jugador con más goles en ese partido
    # (simplificación: MVP = jugador con más goles en el partido más reciente)
    goles_subquery = db.query(
        EventoPartido.id_jugador,
        func.count(EventoPartido.id_evento).label('goles'),
        func.avg(EventoPartido.minuto).label('minuto_promedio')
    ).filter(
        EventoPartido.tipo_evento == TIPO_GOL,
        EventoPartido.id_partido == partido_recente.id_partido
    ).group_by(EventoPartido.id_jugador).subquery()

    mvp_data = db.query(
        Jugador,
        Usuario.nombre,
        Equipo.nombre.label('nombre_equipo'),
        Equipo.escudo.label('escudo_equipo'),
        goles_subquery.c.goles,
    ).join(
        Usuario, Jugador.id_usuario == Usuario.id_usuario
    ).join(
        Equipo, Jugador.id_equipo == Equipo.id_equipo
    ).join(
        goles_subquery, Jugador.id_jugador == goles_subquery.c.id_jugador
    ).filter(
        EventoPartido.id_partido == partido_recente.id_partido
    ).order_by(
        goles_subquery.c.goles.desc()
    ).first()

    if not mvp_data:
        return None

    jugador, nombre, nombre_equipo, escudo, goles = mvp_data

    # Calcular rating simplificado (base 7.0 + goles * 0.5)
    rating = round(7.0 + (goles * 0.5), 1)

    # Contar asistencias en el partido
    asistencias = db.query(EventoPartido).filter(
        EventoPartido.tipo_evento == TIPO_ASISTENCIA,
        EventoPartido.id_partido == partido_recente.id_partido,
        EventoPartido.id_jugador == jugador.id_jugador
    ).count()

    return MatchdayMVPResponse(
        id_jugador=jugador.id_jugador,
        id_usuario=jugador.id_usuario,
        nombre=nombre,
        nombre_equipo=nombre_equipo,
        escudo_equipo=escudo,
        rating=rating,
        goles=goles,
        asistencias=asistencias,
        jornada=1,  # Simplificado
    )


@router.get("/liga/{liga_id}/equipos/goles", response_model=List[TeamGoalsStatsResponse])
def obtener_estadisticas_goles_equipos(liga_id: int, db: Session = Depends(get_db)):
    """
    Obtener estadísticas de goles por equipo.

    Parámetros:
        - liga_id (int): ID de la liga (path parameter)
        - db (Session): Sesión de base de datos

    Returns:
        List[TeamGoalsStatsResponse]: Estadísticas de goles por equipo

    Requiere autenticación: No
    Roles permitidos: Público
    """
    # Verificar que la liga existe
    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    # Obtener todos los equipos de la liga
    equipos = db.query(Equipo).filter(Equipo.id_liga == liga_id).all()

    estadisticas = []
    for equipo in equipos:
        # Partidos del equipo (como local o visitante)
        partidos_local = db.query(Partido).filter(
            Partido.id_liga == liga_id,
            Partido.id_equipo_local == equipo.id_equipo,
            Partido.estado == 'FINALIZADO'
        ).all()

        partidos_visitante = db.query(Partido).filter(
            Partido.id_liga == liga_id,
            Partido.id_equipo_visitante == equipo.id_equipo,
            Partido.estado == 'FINALIZADO'
        ).all()

        partidos_jugados = len(partidos_local) + len(partidos_visitante)

        # Goles a favor (como local)
        goles_favor_local = 0
        for partido in partidos_local:
            eventos = db.query(EventoPartido).filter(
                EventoPartido.id_partido == partido.id_partido,
                EventoPartido.tipo_evento == TIPO_GOL,
                EventoPartido.id_equipo == equipo.id_equipo
            ).all()
            goles_favor_local += len(eventos)

        # Goles a favor (como visitante)
        goles_favor_visitante = 0
        for partido in partidos_visitante:
            eventos = db.query(EventoPartido).filter(
                EventoPartido.id_partido == partido.id_partido,
                EventoPartido.tipo_evento == TIPO_GOL,
                EventoPartido.id_equipo == equipo.id_equipo
            ).all()
            goles_favor_visitante += len(eventos)

        goles_favor = goles_favor_local + goles_favor_visitante

        # Goles en contra (goles del oponente)
        goles_contra = 0

        # Como local: goles del visitante
        for partido in partidos_local:
            eventos = db.query(EventoPartido).filter(
                EventoPartido.id_partido == partido.id_partido,
                EventoPartido.tipo_evento == TIPO_GOL,
                EventoPartido.id_equipo == partido.id_equipo_visitante
            ).all()
            goles_contra += len(eventos)

        # Como visitante: goles del local
        for partido in partidos_visitante:
            eventos = db.query(EventoPartido).filter(
                EventoPartido.id_partido == partido.id_partido,
                EventoPartido.tipo_evento == TIPO_GOL,
                EventoPartido.id_equipo == partido.id_equipo_local
            ).all()
            goles_contra += len(eventos)

        diferencia_goles = goles_favor - goles_contra
        promedio_goles = round(goles_favor / partidos_jugados, 2) if partidos_jugados > 0 else 0

        estadisticas.append(
            TeamGoalsStatsResponse(
                id_equipo=equipo.id_equipo,
                nombre=equipo.nombre,
                escudo=equipo.escudo,
                goles_favor=goles_favor,
                goles_contra=goles_contra,
                diferencia_goles=diferencia_goles,
                promedio_goles_favor=promedio_goles,
                partidos_jugados=partidos_jugados,
            )
        )

    # Ordenar por goles a favor descendente
    estadisticas.sort(key=lambda x: x.goles_favor, reverse=True)

    return estadisticas
