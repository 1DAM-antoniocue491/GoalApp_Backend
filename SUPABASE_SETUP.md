# Configuración de Supabase Storage para Imágenes

## Resumen

El sistema de imágenes ha sido migrado de almacenamiento local en filesystem a **Supabase Storage**. Esto resuelve el problema de pérdida de imágenes en cada deploy de Render.

## Cambios Realizados

### 1. Nuevo Servicio: `supabase_storage_service.py`
- `app/api/services/supabase_storage_service.py`
- Método `upload_file()` para subir archivos (usuarios, equipos, ligas)
- Método `delete_file()` para eliminar archivos
- Método `get_public_url()` para obtener URLs públicas

### 2. Router Actualizado: `imagenes.py`
- Todos los endpoints ahora usan Supabase Storage
- Endpoints actualizados:
  - `POST /imagenes/usuarios/{usuario_id}` - Subir imagen de perfil
  - `POST /imagenes/equipos/{equipo_id}` - Subir escudo de equipo
  - `POST /imagenes/ligas/{liga_id}` - Subir logo de liga
  - `GET /imagenes/{subfolder}/{filename}` - Obtener URL pública
  - `DELETE /imagenes/usuarios/{usuario_id}` - Eliminar imagen

### 3. Dependencias Añadidas
- `supabase` paquete añadido a `requirements.txt`

## Pasos de Configuración

### Paso 1: Obtener Credenciales de Supabase

1. Ve al dashboard de Supabase: https://app.supabase.com
2. Selecciona tu proyecto GoalApp
3. Ve a **Project Settings** (engranaje abajo a la izquierda)
4. Ve a **API**
5. Copia las siguientes credenciales:
   - **Project URL** (ej: `https://xyzgoalapp.supabase.co`)
   - **Service Role Key** (clave secreta - no la anon key!)

### Paso 2: Configurar Variables de Entorno

Edita el archivo `.env` y añade:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (tu service role key)
STORAGE_BUCKET_NAME=equipos-imagenes
```

### Paso 3: Crear Bucket en Supabase

**Opción A: Desde el Dashboard (Recomendado)**

1. Ve a **Storage** en el sidebar izquierdo
2. Click en **New Bucket**
3. Nombre: `equipos-imagenes`
4. Marca **Public bucket**
5. File size limit: `5242880` bytes (5MB)
6. Allowed MIME types: `image/jpeg,image/png,image/webp`
7. Click en **Create bucket**

**Opción B: Usando el Script Python**

```bash
cd GoalApp_Backend
python scripts/crear_bucket_supabase.py
```

> Nota: El script requiere tener `SUPABASE_URL` y `SUPABASE_KEY` configuradas en `.env`

### Paso 4: Configurar Políticas RLS

1. Ve a **SQL Editor** en Supabase
2. Ejecuta el siguiente SQL:

```sql
-- Política de lectura pública
CREATE POLICY "equipos-imagenes-public-read" ON storage.objects
FOR SELECT
USING (bucket_id = 'equipos-imagenes');

-- Política de insert (autenticados)
CREATE POLICY "equipos-imagenes-auth-insert" ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = 'equipos-imagenes');

-- Política de delete (autenticados)
CREATE POLICY "equipos-imagenes-auth-delete" ON storage.objects
FOR DELETE
USING (bucket_id = 'equipos-imagenes');
```

### Paso 5: Instalar Dependencias

```bash
cd GoalApp_Backend
pip install -r requirements.txt
```

### Paso 6: Probar la Integración

1. Inicia el backend: `uvicorn app.main:app --reload`
2. Usa el endpoint `POST /imagenes/equipos/{equipo_id}` para subir una imagen
3. Verifica que la URL devuelta es una URL pública de Supabase (comienza con `https://`)

## URLs Públicas de Ejemplo

Las imágenes almacenadas tendrán URLs como:

```
https://<proyecto>.supabase.co/storage/v1/object/public/equipos-imagenes/equipo_5/a1b2c3d4.webp
```

## Migración de Imágenes Existentes

Las imágenes actuales en el filesystem local seguirán funcionando si sus URLs se almacenan en la base de datos. Para migrar completamente:

1. Subir cada imagen local a Supabase Storage
2. Actualizar el campo `escudo`/`imagen_url`/`logo_url` con la nueva URL pública
3. Eliminar archivo local (opcional)

## Troubleshooting

### Error: "SUPABASE_URL y SUPABASE_KEY deben estar configuradas"
- Verifica que `.env` tiene las variables configuradas
- Reinicia el servidor después de cambiar `.env`

### Error: "Bucket not found"
- El bucket `equipos-imagenes` no existe
- Créalo desde el dashboard o ejecuta el script

### Error: "permission denied"
- Las políticas RLS no están configuradas correctamente
- Ejecuta el SQL del Paso 4

### Imágenes no se muestran
- Verifica que el bucket es público
- Comprueba que la URL en la BD es completa (comienza con `https://`)
