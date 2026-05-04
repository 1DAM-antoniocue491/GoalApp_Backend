# app/api/routers/imagenes.py
"""
Router de Imágenes - Gestión de subida y recuperación de imágenes.
Endpoints para subir y obtener imágenes de usuarios y equipos.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.api.services.imagen_service import delete_image, get_image_path
from app.api.services.supabase_storage_service import get_storage_service
from app.api.services.usuario_service import actualizar_usuario
from app.config import settings

import os

# Configuración del router
router = APIRouter(
    prefix="/imagenes",
    tags=["Imágenes"]
)


@router.post("/usuarios/{usuario_id}", summary="Subir imagen de perfil de usuario")
async def subir_imagen_usuario(
    usuario_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Sube una imagen de perfil para un usuario.

    Solo el propio usuario o un administrador puede subir la imagen.

    Parámetros:
        - usuario_id (int): ID del usuario
        - file (UploadFile): Archivo de imagen (JPEG, PNG, WebP)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: URL pública de la imagen guardada en Supabase Storage

    Requiere autenticación: Sí
    """
    # Verificar que el usuario puede modificar su propia imagen
    if current_user.id_usuario != usuario_id:
        es_admin = any(rol.nombre == "admin" for rol in current_user.roles)
        if not es_admin:
            raise HTTPException(403, "No tienes permiso para modificar esta imagen")

    # Subir a Supabase Storage
    storage_service = get_storage_service()
    result = await storage_service.upload_file(file, "usuarios", usuario_id)

    if not result["success"]:
        raise HTTPException(500, f"Error al subir imagen: {result['error']}")

    # Actualizar usuario con la URL pública
    from app.schemas.usuario import UsuarioUpdate
    actualizar_usuario(db, usuario_id, UsuarioUpdate(imagen_url=result["public_url"]))

    return {"imagen_url": result["public_url"]}


@router.post("/equipos/{equipo_id}", summary="Subir escudo de equipo")
async def subir_imagen_equipo(
    equipo_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Sube un escudo para un equipo.

    Solo entrenadores, delegados o administradores pueden subir el escudo.

    Parámetros:
        - equipo_id (int): ID del equipo
        - file (UploadFile): Archivo de imagen (JPEG, PNG, WebP)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: URL pública de la imagen guardada en Supabase Storage

    Requiere autenticación: Sí
    """
    from app.models.equipo import Equipo

    # Verificar permisos: admin, entrenador o delegado del equipo
    es_admin = any(rol.nombre == "admin" for rol in current_user.roles)

    equipo = db.query(Equipo).filter(Equipo.id_equipo == equipo_id).first()
    if not equipo:
        raise HTTPException(404, "Equipo no encontrado")

    if not es_admin:
        if equipo.id_entrenador != current_user.id_usuario and equipo.id_delegado != current_user.id_usuario:
            raise HTTPException(403, "No tienes permiso para modificar este equipo")

    # Subir a Supabase Storage
    storage_service = get_storage_service()
    result = await storage_service.upload_file(file, "equipos", equipo_id)

    if not result["success"]:
        raise HTTPException(500, f"Error al subir imagen: {result['error']}")

    # Actualizar equipo con la URL pública
    equipo.escudo = result["public_url"]
    db.commit()

    return {"imagen_url": result["public_url"]}


@router.post("/ligas/{liga_id}", summary="Subir logo de liga")
async def subir_imagen_liga(
    liga_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Sube un logo para una liga.

    Solo administradores o usuarios con rol en la liga pueden subir el logo.

    Parámetros:
        - liga_id (int): ID de la liga
        - file (UploadFile): Archivo de imagen (JPEG, PNG, WebP)
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: URL pública de la imagen guardada en Supabase Storage

    Requiere autenticación: Sí
    """
    from app.models.liga import Liga
    from app.models.usuario_rol import UsuarioRol

    # Verificar permisos: admin o usuario con rol en la liga
    es_admin = any(rol.nombre == "admin" for rol in current_user.roles)

    liga = db.query(Liga).filter(Liga.id_liga == liga_id).first()
    if not liga:
        raise HTTPException(404, "Liga no encontrada")

    if not es_admin:
        # Verificar si el usuario tiene algún rol en esta liga
        usuario_rol = db.query(UsuarioRol).filter(
            UsuarioRol.id_usuario == current_user.id_usuario,
            UsuarioRol.id_liga == liga_id
        ).first()
        if not usuario_rol:
            raise HTTPException(403, "No tienes permiso para modificar esta liga")

    # Subir a Supabase Storage
    storage_service = get_storage_service()
    result = await storage_service.upload_file(file, "ligas", liga_id)

    if not result["success"]:
        raise HTTPException(500, f"Error al subir imagen: {result['error']}")

    # Actualizar liga con la URL pública
    liga.logo_url = result["public_url"]
    db.commit()

    return {"imagen_url": result["public_url"]}


@router.get("/{subfolder}/{filename}", summary="Obtener imagen")
async def obtener_imagen(
    subfolder: str,
    filename: str
):
    """
    Obtiene la URL pública de una imagen almacenada en Supabase Storage.

    Parámetros:
        - subfolder (str): Subcarpeta (usuarios, equipos)
        - filename (str): Nombre del archivo

    Returns:
        dict: URL pública de la imagen

    Requiere autenticación: No
    """
    # Construir path relativo y obtener URL pública
    file_path = f"{subfolder}/{filename}"
    storage_service = get_storage_service()
    public_url = storage_service.get_public_url(file_path)

    if not public_url:
        raise HTTPException(404, "Imagen no encontrada")

    return JSONResponse(content={"url": public_url})


@router.delete("/usuarios/{usuario_id}", summary="Eliminar imagen de perfil")
async def eliminar_imagen_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Elimina la imagen de perfil de un usuario.

    Solo el propio usuario o un administrador puede eliminar la imagen.

    Parámetros:
        - usuario_id (int): ID del usuario
        - db (Session): Sesión de base de datos
        - current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación

    Requiere autenticación: Sí
    """
    from app.models.usuario import Usuario

    # Verificar permisos
    if current_user.id_usuario != usuario_id:
        es_admin = any(rol.nombre == "admin" for rol in current_user.roles)
        if not es_admin:
            raise HTTPException(403, "No tienes permiso para eliminar esta imagen")

    # Obtener usuario
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")

    # Eliminar de Supabase Storage
    if usuario.imagen_url:
        storage_service = get_storage_service()
        storage_service.delete_file(usuario.imagen_url)
        usuario.imagen_url = None
        db.commit()

    return {"mensaje": "Imagen eliminada correctamente"}