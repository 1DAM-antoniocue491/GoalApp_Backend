-- ============================================
-- SUPABASE MIGRATION: Remove unique constraint from ligas.nombre
-- ============================================
-- Description: Removes the unique constraint from the 'nombre' column in the 'ligas' table
--              to allow multiple leagues with the same name (but different owners/users)
--
-- Database: PostgreSQL (Supabase)
-- Schema: public
-- Table: ligas
--
-- Reason: The backend now validates unique league names per user at the service layer
--         instead of enforcing it at the database level. This allows:
--         - Multiple users creating leagues with the same name (e.g., "Liga Pepe")
--         - Users cannot create multiple leagues with the same name themselves
--         - Validation logic in liga_service.py and invitacion_service.py
--
-- Migration Version: 1.0
-- Created: 2026-05-01
-- ============================================

-- ============================================
-- How to apply this migration:
-- ============================================
-- 1. Go to your Supabase dashboard: https://supabase.com/dashboard
-- 2. Select your project
-- 3. Navigate to SQL Editor
-- 4. Copy and paste the DROP CONSTRAINT statement from STEP 1
-- 5. Execute the SQL
-- 6. Verify with the query in STEP 2 (should return 0 rows)
-- ============================================

-- ============================================================================
-- STEP 1: Drop the unique constraint (if exists)
-- ============================================================================
-- Uses IF EXISTS to safely handle cases where the constraint might not exist
-- This prevents errors when running the migration multiple times or in different environments
-- The constraint name follows PostgreSQL naming convention: tablename_columnname_key

ALTER TABLE public.ligas DROP CONSTRAINT IF EXISTS ligas_nombre_key;

-- ============================================================================
-- STEP 2: Verification Query
-- ============================================================================
-- Run this query to verify the constraint has been successfully removed
-- Expected result: 0 rows (constraint does not exist anymore)

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

-- Expected: No rows returned if migration was successful

-- ============================================================================
-- STEP 3: Rollback Commands (for reference)
-- ============================================================================
-- If you need to rollback this migration, run the following SQL:

-- ROLLBACK COMMAND (do not execute during normal migration):
-- CREATE UNIQUE INDEX ligas_nombre_key ON ligas USING btree (nombre);

-- After creating the index, you may need to add the constraint:
-- ALTER TABLE ligas ADD CONSTRAINT ligas_nombre_key UNIQUE USING INDEX ligas_nombre_key;

-- ============================================================================
-- Notes:
-- - The 'nombre' column in 'ligas' table is no longer unique
-- - Multiple leagues can now share the same name (distinguished by owner/user)
-- - This change affects all leagues across the system
-- - No data loss occurs during this migration
-- ============================================================================
