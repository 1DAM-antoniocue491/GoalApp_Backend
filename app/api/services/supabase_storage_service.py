# app/api/services/supabase_storage_service.py
"""
Servicio de almacenamiento en Supabase Storage.
Maneja la subida, eliminación y obtención de URLs públicas de imágenes.
"""
import os
import uuid
from supabase import create_client, Client
from fastapi import UploadFile, HTTPException

from app.config import settings


class SupabaseStorageService:
    """Servicio para gestionar archivos en Supabase Storage"""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("STORAGE_BUCKET_NAME", "equipos-imagenes")

        if not self.supabase_url or not self.supabase_key:
            raise HTTPException(
                status_code=500,
                detail="SUPABASE_URL y SUPABASE_KEY deben estar configuradas en .env"
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    async def upload_file(self, file: UploadFile, folder: str, entity_id: int) -> dict:
        """
        Sube una imagen a Supabase Storage.

        Args:
            file: Archivo subido
            folder: Carpeta para organizar (ej: "usuarios", "equipos", "ligas")
            entity_id: ID de la entidad para organizar en subcarpeta

        Returns:
            dict: {"success": bool, "path": str, "public_url": str, "error": str|None}
        """
        try:
            # Validar imagen
            self._validate_image(file)

            # Generar nombre único: equipo_5/a1b2c3d4.webp
            ext = self._get_extension(file.filename)
            unique_filename = f"{folder}_{entity_id}/{uuid.uuid4()}{ext}"

            # Leer contenido
            file_content = await file.read()
            content_type = file.content_type or "image/webp"

            # Validar tamaño (5MB max)
            if len(file_content) > settings.MAX_IMAGE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo excede el tamaño máximo de {settings.MAX_IMAGE_SIZE // 1024 // 1024}MB"
                )

            # Subir a Supabase
            response = self.client.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",
                }
            )

            # Obtener URL pública
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(unique_filename)

            return {
                "success": True,
                "path": unique_filename,
                "public_url": public_url,
                "error": None
            }

        except HTTPException:
            raise
        except Exception as e:
            return {
                "success": False,
                "path": None,
                "public_url": None,
                "error": str(e)
            }

    def delete_file(self, file_path: str) -> dict:
        """
        Elimina un archivo del bucket.

        Args:
            file_path: Ruta del archivo en el bucket (ej: equipo_5/abc.webp)

        Returns:
            dict: {"success": bool, "error": str|None}
        """
        try:
            if not file_path:
                return {"success": False, "error": "No file path provided"}

            # Limpiar el path si viene con formato de URL
            clean_path = file_path
            if clean_path.startswith("/uploads/"):
                clean_path = clean_path.replace("/uploads/", "")

            self.client.storage.from_(self.bucket_name).remove([clean_path])

            return {"success": True, "error": None}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_public_url(self, file_path: str) -> str | None:
        """
        Obtiene la URL pública de un archivo.

        Args:
            file_path: Ruta del archivo en el bucket

        Returns:
            str | None: URL pública o None si hay error
        """
        try:
            if not file_path:
                return None

            # Si ya es una URL completa, retornarla
            if file_path.startswith("http"):
                return file_path

            # Limpiar path
            clean_path = file_path
            if clean_path.startswith("/uploads/"):
                clean_path = clean_path.replace("/uploads/", "")

            return self.client.storage.from_(self.bucket_name).get_public_url(clean_path)

        except Exception:
            return None

    def _validate_image(self, file: UploadFile) -> None:
        """Valida que el archivo sea una imagen permitida"""
        allowed_types = {"image/jpeg", "image/png", "image/webp"}

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido. Tipos: {', '.join(allowed_types)}"
            )

    def _get_extension(self, filename: str | None) -> str:
        """Obtiene la extensión del archivo o default .webp"""
        if filename and "." in filename:
            ext = os.path.splitext(filename)[1].lower()
            if ext in {".jpg", ".jpeg", ".png", ".webp"}:
                return ext
        return ".webp"


# Singleton
_storage_service: SupabaseStorageService | None = None


def get_storage_service() -> SupabaseStorageService:
    """Obtiene la instancia del servicio de almacenamiento"""
    global _storage_service

    if _storage_service is None:
        try:
            _storage_service = SupabaseStorageService()
        except HTTPException:
            raise

    return _storage_service
