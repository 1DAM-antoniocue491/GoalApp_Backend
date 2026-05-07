-- Migración 007: Añadir columna updated_at a convocatoria_partido para optimistic locking
-- Fecha: 2026-05-08
-- Propósito: Permitir detección de ediciones concurrentes en convocatorias

-- Añadir columna updated_at
ALTER TABLE convocatoria_partido
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

-- Establecer el valor por defecto para registros existentes (igual que created_at)
UPDATE convocatoria_partido
SET updated_at = created_at
WHERE updated_at IS NULL;

-- Hacer la columna NOT NULL
ALTER TABLE convocatoria_partido
ALTER COLUMN updated_at SET NOT NULL;

-- Añadir default para nuevos registros
ALTER TABLE convocatoria_partido
ALTER COLUMN updated_at SET DEFAULT NOW();

-- Comentario descriptivo
COMMENT ON COLUMN convocatoria_partido.updated_at IS 'Fecha y hora de última actualización (para optimistic locking)';
