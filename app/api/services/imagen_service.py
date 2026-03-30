# app/api/services/imagen_service.py
"""
Servicio de gestión de imágenes.
Maneja la subida, almacenamiento y recuperación de imágenes en el servidor.
"""
import os
import uuid
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import settings


# Extensiones permitidas
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
# Tipos MIME permitidos
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def ensure_upload_dir() -> str:
    """
    Asegura que el directorio de uploads existe.

    Returns:
        str: Ruta al directorio de uploads
    """
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir


def validate_image(file: UploadFile) -> None:
    """
    Valida que el archivo sea una imagen válida.

    Args:
        file (UploadFile): Archivo subido

    Raises:
        HTTPException: Si el archivo no es válido
    """
    # Validar tipo MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    # Validar extensión
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Extensión no permitida. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
            )


async def save_image(file: UploadFile, subfolder: str = "") -> str:
    """
    Guarda una imagen en el servidor.

    Args:
        file (UploadFile): Archivo subido
        subfolder (str): Subcarpeta dentro de uploads (ej: "usuarios", "equipos")

    Returns:
        str: URL relativa de la imagen guardada

    Raises:
        HTTPException: Si hay error al guardar
    """
    # Validar imagen
    validate_image(file)

    # Asegurar directorio
    upload_dir = ensure_upload_dir()
    if subfolder:
        upload_dir = os.path.join(upload_dir, subfolder)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

    # Generar nombre único
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    # Guardar archivo
    try:
        content = await file.read()
        # Validar tamaño
        if len(content) > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo excede el tamaño máximo permitido ({settings.MAX_IMAGE_SIZE // 1024 // 1024}MB)"
            )

        with open(filepath, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la imagen: {str(e)}")

    # Retornar URL relativa
    if subfolder:
        return f"/uploads/{subfolder}/{filename}"
    return f"/uploads/{filename}"


def delete_image(image_url: str) -> bool:
    """
    Elimina una imagen del servidor.

    Args:
        image_url (str): URL relativa de la imagen

    Returns:
        bool: True si se eliminó correctamente
    """
    if not image_url:
        return False

    try:
        # Convertir URL a ruta del sistema
        filepath = image_url.lstrip("/uploads/")
        filepath = os.path.join(settings.UPLOAD_DIR, filepath)

        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass

    return False


def get_image_path(image_url: str) -> str | None:
    """
    Obtiene la ruta física de una imagen.

    Args:
        image_url (str): URL relativa de la imagen

    Returns:
        str | None: Ruta física de la imagen o None si no existe
    """
    if not image_url:
        return None

    try:
        filepath = image_url.lstrip("/uploads/")
        filepath = os.path.join(settings.UPLOAD_DIR, filepath)

        if os.path.exists(filepath):
            return filepath
    except Exception:
        pass

    return None