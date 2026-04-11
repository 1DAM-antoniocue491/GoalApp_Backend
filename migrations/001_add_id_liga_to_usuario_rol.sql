-- Migration: Add id_liga to usuario_rol table
-- Description: Associates user roles with specific leagues, allowing users
--              to have different roles in different leagues.
-- Author: System
-- Date: 2026-04-10

-- IMPORTANT: Run this migration in the following order:
-- 1. Add id_liga column with NULL allowed
-- 2. Update existing records to assign id_liga = 1
-- 3. Make id_liga NOT NULL
-- 4. Add foreign key constraint

-- ============================================================
-- STEP 1: Add id_liga column (allows NULL temporarily)
-- ============================================================

ALTER TABLE usuario_rol
ADD COLUMN id_liga INT NULL;

-- ============================================================
-- STEP 2: Update existing records
-- Assign all existing usuario_rol records to liga 1
-- Adjust the id_liga value if your first liga has a different ID
-- ============================================================

-- First, verify the first liga exists and get its ID
-- SELECT id_liga FROM ligas ORDER BY id_liga LIMIT 1;

-- Update all existing usuario_rol records to reference liga 1
-- NOTE: Adjust this query based on your actual data:
-- - If you have multiple ligas and want to distribute users, use a more complex UPDATE
-- - If your first liga has a different ID, replace '1' with that ID

UPDATE usuario_rol
SET id_liga = 1
WHERE id_liga IS NULL;

-- ============================================================
-- STEP 3: Make id_liga NOT NULL
-- ============================================================

ALTER TABLE usuario_rol
MODIFY COLUMN id_liga INT NOT NULL;

-- ============================================================
-- STEP 4: Add foreign key constraint
-- ============================================================

ALTER TABLE usuario_rol
ADD CONSTRAINT fk_usuario_rol_liga
FOREIGN KEY (id_liga) REFERENCES ligas(id_liga)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- ============================================================
-- VERIFICATION QUERIES
-- Run these to verify the migration was successful
-- ============================================================

-- Check the table structure
-- DESCRIBE usuario_rol;

-- Check that all records have id_liga assigned
-- SELECT COUNT(*) FROM usuario_rol WHERE id_liga IS NULL;  -- Should return 0

-- Verify foreign key constraint exists
-- SELECT * FROM information_schema.TABLE_CONSTRAINTS
-- WHERE TABLE_NAME = 'usuario_rol' AND CONSTRAINT_TYPE = 'FOREIGN KEY';

-- ============================================================
-- ROLLBACK (in case you need to revert this migration)
-- ============================================================

-- To rollback, run:
-- ALTER TABLE usuario_rol DROP FOREIGN KEY fk_usuario_rol_liga;
-- ALTER TABLE usuario_rol DROP COLUMN id_liga;