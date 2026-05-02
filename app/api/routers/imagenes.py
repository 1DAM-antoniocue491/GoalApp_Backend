# app/api/routers/imagenes.py
"""
Router de Imágenes - Gestión de subida y recuperación de imágenes.
Endpoints para subir y obtener imágenes de usuarios y equipos.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.api.services.imagen_service import save_image, delete_image, get_image_path
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
        dict: URL de la imagen guardada

    Requiere autenticación: Sí
    """
    # Verificar que el usuario puede modificar su propia imagen
    # (el propio usuario o un admin)
    if current_user.id_usuario != usuario_id:
        # Verificar si es admin
        es_admin = any(rol.nombre == "admin" for rol in current_user.roles)
        if not es_admin:
            raise HTTPException(403, "No tienes permiso para modificar esta imagen")

    # Guardar imagen
    image_url = await save_image(file, subfolder="usuarios")

    # Actualizar usuario con la nueva imagen
    from app.schemas.usuario import UsuarioUpdate
    actualizar_usuario(db, usuario_id, UsuarioUpdate(imagen_url=image_url))

    return {"imagen_url": image_url}


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
        dict: URL de la imagen guardada

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

    # Guardar imagen
    image_url = await save_image(file, subfolder="equipos")

    # Actualizar equipo con el nuevo escudo
    equipo.escudo = image_url
    db.commit()

    return {"imagen_url": image_url}


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
        dict: URL de la imagen guardada

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

    # Guardar imagen
    image_url = await save_image(file, subfolder="ligas")

    # Actualizar liga con el nuevo logo
    liga.logo_url = image_url
    db.commit()

    return {"imagen_url": image_url}


@router.get("/{subfolder}/{filename}", summary="Obtener imagen")
async def obtener_imagen(
    subfolder: str,
    filename: str
):
    """
    Obtiene una imagen almacenada en el servidor.

    Parámetros:
        - subfolder (str): Subcarpeta (usuarios, equipos)
        - filename (str): Nombre del archivo

    Returns:
        FileResponse: Archivo de imagen

    Requiere autenticación: No
    """
    image_url = f"/uploads/{subfolder}/{filename}"
    filepath = get_image_path(image_url)

    if not filepath:
        raise HTTPException(404, "Imagen no encontrada")

    return FileResponse(filepath)


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

    # Eliminar archivo
    if usuario.imagen_url:
        delete_image(usuario.imagen_url)
        usuario.imagen_url = None
        db.commit()

    return {"mensaje": "Imagen eliminada correctamente"}