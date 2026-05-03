# app/config.py
"""
Configuración centralizada de la aplicación.
Lee variables de entorno desde el archivo .env (obligatorio).
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings.
    
    Todas las variables se leen desde el archivo .env ubicado en backend/.env
    Si el archivo .env no existe o faltan variables, la aplicación fallará.
    
    Para crear tu archivo .env:
    1. Copia backend/.env.example a backend/.env
    2. Modifica los valores según tu entorno
    3. NUNCA subas el archivo .env a Git (está en .gitignore)
    
    Attributes:
        DATABASE_URL (str): URL de conexión a PostgreSQL
        DATABASE_ECHO (bool): Si mostrar queries SQL en consola
        SECRET_KEY (str): Clave secreta para JWT (64 bytes)
        ALGORITHM (str): Algoritmo de encriptación JWT (HS256)
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Tiempo de expiración del token
        APP_NAME (str): Nombre de la aplicación
        API_VERSION (str): Versión de la API
        ENVIRONMENT (str): Entorno de ejecución (development/production)
        PORT (int): Puerto del servidor
        HOST (str): Host del servidor
        CORS_ORIGINS (str): Orígenes permitidos para CORS (separados por comas)
        LOG_LEVEL (str): Nivel de logging (DEBUG/INFO/WARNING/ERROR)
    """
    
    # ============================================================
    # BASE DE DATOS
    # ============================================================
    DATABASE_URL: str  # Requerido, sin valor por defecto
    DATABASE_ECHO: bool  # Requerido, sin valor por defecto
    
    # ============================================================
    # SEGURIDAD JWT
    # ============================================================
    SECRET_KEY: str  # Requerido, sin valor por defecto
    ALGORITHM: str  # Requerido, sin valor por defecto
    ACCESS_TOKEN_EXPIRE_MINUTES: int  # Requerido, sin valor por defecto
    
    # ============================================================
    # APLICACIÓN
    # ============================================================
    APP_NAME: str  # Requerido, sin valor por defecto
    API_VERSION: str  # Requerido, sin valor por defecto
    ENVIRONMENT: str  # Requerido, sin valor por defecto
    PORT: int  # Requerido, sin valor por defecto
    HOST: str  # Requerido, sin valor por defecto
    
    # ============================================================
    # CORS
    # ============================================================
    CORS_ORIGINS: str  # Requerido, sin valor por defecto (separado por comas)
    
    # ============================================================
    # LOGGING
    # ============================================================
    LOG_LEVEL: str  # Requerido, sin valor por defecto

    # ============================================================
    # EMAIL (SMTP)
    # ============================================================
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_SSL: bool = False  # Usar True para SSL puro (puerto 465), False para TLS (puerto 587)
    EMAIL_FROM: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # ============================================================
    # ALMACENAMIENTO DE IMÁGENES
    # ============================================================
    UPLOAD_DIR: str = "uploads"  # Directorio para almacenar imágenes
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB máximo
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"
    
    model_config = {
        "env_file": ".env",  # Lee desde backend/.env
        "env_file_encoding": "utf-8",
        "case_sensitive": True, # Las variables son case-sensitive
    }
    
    def get_cors_origins_list(self) -> List[str]:
        """
        Convierte la cadena de CORS_ORIGINS en una lista.
        
        El archivo .env almacena CORS_ORIGINS como string separado por comas:
        CORS_ORIGINS=http://localhost:3000,http://localhost:8081
        
        Esta función lo convierte en lista para usar en FastAPI:
        ["http://localhost:3000", "http://localhost:8081"]
        
        Returns:
            List[str]: Lista de orígenes permitidos
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna una instancia única de Settings (singleton).
    Se cachea para evitar leer el archivo .env múltiples veces.
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()
