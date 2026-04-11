# app/models/usuario.py
"""
Modelo de Usuario para la base de datos.
Representa los usuarios registrados en el sistema con sus credenciales y datos básicos.
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database.connection import Base


class GeneroEnum(str, enum.Enum):
    """Enumeración para el género del usuario."""
    masculino = "masculino"
    femenino = "femenino"
    otro = "otro"


class Usuario(Base):
    """
    Modelo ORM para la tabla 'usuarios'.

    Un usuario puede tener múltiples roles (Admin, Coach, Delegate, Player, Viewer)
    y puede estar asociado a equipos como jugador, entrenador o delegado.

    Attributes:
        id_usuario (int): Identificador único del usuario (Primary Key)
        nombre (str): Nombre completo del usuario (máx. 100 caracteres)
        email (str): Correo electrónico único del usuario (máx. 100 caracteres)
        contraseña_hash (str): Hash bcrypt de la contraseña (máx. 255 caracteres)
        genero (GeneroEnum | None): Género del usuario (opcional)
        telefono (str | None): Número de teléfono (máx. 20 caracteres, opcional)
        fecha_nacimiento (date | None): Fecha de nacimiento (opcional)
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
        roles (list): Lista de roles asignados al usuario (relación N:N)
    """
    __tablename__ = "usuarios"

    # Clave primaria
    id_usuario = Column(Integer, primary_key=True)

    # Información básica
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)  # Email único para login
    contraseña_hash = Column(String(255), nullable=False)  # Almacenado con bcrypt

    # Información opcional del perfil
    genero = Column(Enum(GeneroEnum), nullable=True)  # Género del usuario
    telefono = Column(String(20), nullable=True)  # Número de teléfono
    fecha_nacimiento = Column(Date, nullable=True)  # Fecha de nacimiento
    imagen_url = Column(String(255), nullable=True)  # URL de la imagen de perfil

    # Auditoría: fechas de creación y actualización
    # Usamos default=func.now() en lugar de server_default para compatibilidad con MySQL 5.5/5.6
    # que no soportan DEFAULT CURRENT_TIMESTAMP para columnas DATETIME
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    # lazy="raise" evita cargas accidentales - usar joinedload() explicitamente cuando se necesite
    roles = relationship("Rol", secondary="usuario_rol", back_populates="usuarios", lazy="raise")
