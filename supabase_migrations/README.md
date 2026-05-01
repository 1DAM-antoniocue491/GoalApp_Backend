# League Name Validation Fix - Migration Guide

## Problem Description

The database had a **UNIQUE constraint** on the `ligas.nombre` field that prevented multiple users from creating leagues with the same name. This was problematic because:

- Multiple users wanted to create leagues with identical names (e.g., "Liga Pepe", "Torneo Verano")
- The constraint enforced uniqueness at the database level, not per user
- Users couldn't create a league with a name they already owned as admin

### Example Issues:
1. User "Pepe" couldn't create "Liga Pepe" if it already existed
2. User "Juan" couldn't create "Liga Pepe" because "Pepe" already had it
3. Pepe couldn't create a second "Liga Pepe" (different season) as admin

## Solution Implemented

**Removed the database-level UNIQUE constraint** and implemented **service-layer validation** that:
- Allows multiple users to create leagues with the same name
- Prevents a single user from creating multiple leagues with the same name (as admin)
- Validates at the point of league creation and invitation acceptance

### Model Changes
**File**: `app/models/liga.py:35`
```python
# Before:
nombre = Column(String(100), unique=True, nullable=False)

# After:
nombre = Column(String(100), nullable=False)  # No longer unique
```

### Service Validation
**File**: `app/api/services/liga_service.py:50-61`
```python
# Verificar si el usuario ya tiene una liga con ese nombre
if id_usuario_creador:
    ligas_usuario = db.query(Liga).join(UsuarioRol).join(Rol).filter(
        Liga.nombre == datos.nombre,
        UsuarioRol.id_usuario == id_usuario_creador,
        UsuarioRol.id_liga == Liga.id_liga,
        Rol.nombre == "admin"
    ).first()
    
    if ligas_usuario:
        raise ValueError(f"Ya tienes una liga con el nombre '{datos.nombre}'")
```

**File**: `app/api/services/invitacion_service.py:359-368`
```python
# Verificar si el usuario ya pertenece a una liga con ese nombre
liga = db.query(Liga).filter(Liga.id_liga == invitacion.id_liga).first()
if liga:
    liga_existente = db.query(UsuarioRol).filter(
        UsuarioRol.id_usuario == usuario_id,
        UsuarioRol.id_liga == liga.id_liga
    ).first()
    
    if liga_existente:
        raise ValueError(f"Ya perteneces a una liga con el nombre '{liga.nombre}'")
```

## How to Apply the Migration

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Navigate to **SQL Editor**
4. Copy and execute the following SQL:

```sql
-- Drop the unique constraint
DROP CONSTRAINT IF EXISTS ligas_nombre_key ON ligas;

-- Verify it was removed (should return 0 rows)
SELECT
    tc.constraint_name,
    tc.table_name,
    kc.column_name
FROM
    information_schema.table_constraints AS tc
JOIN
    information_schema.key_column_usage AS kc
    ON tc.constraint_name = kc.constraint_name
WHERE
    tc.table_name = 'ligas'
    AND tc.constraint_type = 'UNIQUE'
    AND tc.constraint_name = 'ligas_nombre_key';
```

### Option 2: Using psql/Database Client

```bash
psql $DATABASE_URL -c "DROP CONSTRAINT IF EXISTS ligas_nombre_key ON ligas;"
```

## How to Verify Success

Run this query in your Supabase SQL Editor:

```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    kc.column_name
FROM
    information_schema.table_constraints AS tc
JOIN
    information_schema.key_column_usage AS kc
    ON tc.constraint_name = kc.constraint_name
WHERE
    tc.table_name = 'ligas'
    AND tc.constraint_type = 'UNIQUE';
```

**Expected result**: No rows returned (constraint does not exist)

## Test Results

All 3 validation tests pass:

```
tests/unit/test_ligas.py::TestValidacionesUnicasLiga::test_crear_liga_mismo_nombre_admin PASSED
tests/unit/test_ligas.py::TestValidacionesUnicasLiga::test_dos_usuarios_mismo_nombre PASSED
tests/unit/test_ligas.py::TestValidacionesUnicasLiga::test_aceptar_invitacion_ya_pertenece PASSED
```

### Test Coverage:
1. **Same user, same name**: User cannot create two leagues with the same name
2. **Different users, same name**: Multiple users can create leagues with the same name
3. **Invitation validation**: User cannot accept invitation if already in a league with that name

## Rollback Instructions

If you need to rollback this migration:

```sql
-- Recreate the unique constraint
CREATE UNIQUE INDEX ligas_nombre_key ON ligas USING btree (nombre);

-- Add the constraint using the index
ALTER TABLE ligas ADD CONSTRAINT ligas_nombre_key UNIQUE USING INDEX ligas_nombre_key;
```

**Warning**: Before rolling back, ensure no duplicate league names exist across different users, or the migration will fail.

## Database Files Modified

- **Model**: `app/models/liga.py:35` - Removed `unique=True`
- **Service**: `app/api/services/liga_service.py:50-61` - Added per-user validation
- **Service**: `app/api/services/invitacion_service.py:359-368` - Added per-user validation
- **Migration**: `supabase_migrations/remove_unique_constraint_from_ligas.sql` - Database patch

## Migration File

The SQL migration is located at:
```
/home/antonio/Escritorio/GoalApp/GoalApp_Backend/supabase_migrations/remove_unique_constraint_from_ligas.sql
```

This file contains:
- Drop constraint statement (with IF EXISTS for safety)
- Verification query
- Rollback commands (for reference)

## Summary

✅ **Database constraint removed** - Multiple users can now create leagues with the same name  
✅ **Service validation added** - Users cannot create multiple leagues with same name as admin  
✅ **Tests passing** - All 3 validation tests pass successfully  
✅ **Migration ready** - SQL patch ready to apply to Supabase
