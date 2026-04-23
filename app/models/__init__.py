# app/models/__init__.py
"""
Importación centralizada de todos los modelos SQLAlchemy.

Este módulo asegura que todos los modelos se registren en el registry
de SQLAlchemy antes de que se inicialicen los mappers, evitando errores
de resolución de nombres en las relaciones.

Import order matters: models without dependencies first, then dependent models.
"""

# Modelos base sin dependencias de otros modelos
from .usuario import Usuario
from .rol import Rol

# Modelos que dependen solo de usuario/rol
from .usuario_rol import UsuarioRol
from .liga import Liga
from .liga_configuracion import LigaConfiguracion
from .token_recuperacion import TokenRecuperacion

# Modelos que dependen de liga
from .equipo import Equipo
from .jornada import Jornada
from .invitacion import Invitacion
from .usuario_sigue_liga import UsuarioSigueLiga

# Modelos que dependen de equipo y jornada
from .jugador import Jugador
from .partido import Partido
from .formacion import Formacion
from .formacion_equipo import FormacionEquipo

# Modelos que dependen de partido
from .evento_partido import EventoPartido
from .alineacion_partido import AlineacionPartido
from .convocatoria_partido import ConvocatoriaPartido
from .formacion_partido import FormacionPartido
from .posicion_formacion import PosicionFormacion

# Modelos que dependen de notificaciones
from .notificacion import Notificacion

# Exportar todos los modelos para facilitar imports
__all__ = [
    "Usuario",
    "Rol",
    "UsuarioRol",
    "Liga",
    "LigaConfiguracion",
    "TokenRecuperacion",
    "Equipo",
    "Jornada",
    "Invitacion",
    "UsuarioSigueLiga",
    "Jugador",
    "Partido",
    "Formacion",
    "FormacionEquipo",
    "FormacionPartido",
    "EventoPartido",
    "AlineacionPartido",
    "ConvocatoriaPartido",
    "PosicionFormacion",
    "Notificacion",
]
