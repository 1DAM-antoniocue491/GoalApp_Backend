# scripts/crear_bucket_supabase.py
"""
Script para crear el bucket 'equipos-imagenes' en Supabase Storage.
Usa la API REST de Supabase directamente.

Requisitos:
1. Tener las variables de entorno configuradas en .env:
   - SUPABASE_URL
   - SUPABASE_KEY (debe ser service_role key, no anon key)

2. Ejecutar desde el directorio backend:
   python scripts/crear_bucket_supabase.py
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar config
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from app.config import settings

# ============================================================
# CONFIGURACIÓN
# ============================================================

BUCKET_NAME = "equipos-imagenes"
BUCKET_PUBLIC = True

# ============================================================
# FUNCIONES
# ============================================================

def crear_bucket():
    """Crea el bucket en Supabase Storage"""
    url = f"{settings.SUPABASE_URL}/storage/v1/bucket"

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "apikey": settings.SUPABASE_KEY,
    }

    data = {
        "name": BUCKET_NAME,
        "public": BUCKET_PUBLIC,
        "file_size_limit": str(5 * 1024 * 1024),  # 5MB
        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
    }

    print(f"Creando bucket '{BUCKET_NAME}' en {settings.SUPABASE_URL}...")

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"✅ Bucket '{BUCKET_NAME}' creado exitosamente")
        return True
    elif response.status_code == 400:
        print(f"⚠️ El bucket '{BUCKET_NAME}' ya existe o hay un error de configuración")
        print(f"   Respuesta: {response.json()}")
        return False
    else:
        print(f"❌ Error al crear el bucket: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        return False


def crear_politicas_rls():
    """Crea las políticas RLS para el bucket"""
    url = f"{settings.SUPABASE_URL}/rest/v1/rpc/create_bucket_policies"

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "apikey": settings.SUPABASE_KEY,
        "Prefer": "return=minimal",
    }

    # SQL para crear las políticas
    sql = f"""
    DO $$
    BEGIN
        -- Política de lectura pública
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'storage'
            AND tablename = 'objects'
            AND policyname = 'equipos-imagenes-public-read'
        ) THEN
            CREATE POLICY "equipos-imagenes-public-read" ON storage.objects
            FOR SELECT
            USING (bucket_id = '{BUCKET_NAME}');
        END IF;

        -- Política de insert (autenticados)
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'storage'
            AND tablename = 'objects'
            AND policyname = 'equipos-imagenes-auth-insert'
        ) THEN
            CREATE POLICY "equipos-imagenes-auth-insert" ON storage.objects
            FOR INSERT
            WITH CHECK (bucket_id = '{BUCKET_NAME}');
        END IF;

        -- Política de delete (autenticados)
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'storage'
            AND tablename = 'objects'
            AND policyname = 'equipos-imagenes-auth-delete'
        ) THEN
            CREATE POLICY "equipos-imagenes-auth-delete" ON storage.objects
            FOR DELETE
            USING (bucket_id = '{BUCKET_NAME}');
        END IF;
    END $$;
    """

    # Nota: Esto requiere ejecutar el SQL directamente en la BD
    # La API REST no permite ejecutar DDL arbitrario
    print("\n⚠️ Las políticas RLS deben crearse manualmente en el dashboard:")
    print(f"   https://app.supabase.com/project/_/editor")
    print("\nO ejecutar este SQL en el SQL Editor:")
    print(sql)

    return False


def verificar_bucket():
    """Verifica si el bucket existe"""
    url = f"{settings.SUPABASE_URL}/storage/v1/bucket/{BUCKET_NAME}"

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "apikey": settings.SUPABASE_KEY,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Bucket '{BUCKET_NAME}' existe")
        print(f"   Público: {data.get('public', False)}")
        print(f"   Tamaño máximo: {data.get('file_size_limit', 'N/A')} bytes")
        return True
    else:
        print(f"❌ Bucket '{BUCKET_NAME}' no existe")
        return False


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Supabase Storage - Crear Bucket")
    print("=" * 60)

    # Verificar configuración
    if not hasattr(settings, 'SUPABASE_URL') or not settings.SUPABASE_URL:
        print("❌ Error: SUPABASE_URL no configurada en .env")
        sys.exit(1)

    if not hasattr(settings, 'SUPABASE_KEY') or not settings.SUPABASE_KEY:
        print("❌ Error: SUPABASE_KEY no configurada en .env")
        sys.exit(1)

    print(f"\nSupabase URL: {settings.SUPABASE_URL}")
    print(f"Supabase Key: {settings.SUPABASE_KEY[:20]}...")  # Ocultar clave

    # Verificar si ya existe
    print("\n" + "-" * 60)
    if verificar_bucket():
        print("\n✅ El bucket ya existe. No es necesario crearlo.")
    else:
        print("\n" + "-" * 60)
        crear_bucket()

    print("\n" + "=" * 60)
    print("Siguientes pasos:")
    print("1. Crear políticas RLS en el dashboard de Supabase")
    print("2. Agregar STORAGE_BUCKET_NAME=equipos-imagenes al .env")
    print("3. Actualizar imagen_service.py para usar Supabase Storage")
    print("=" * 60)
