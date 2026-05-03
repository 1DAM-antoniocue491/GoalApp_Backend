-- Migración 003 (PostgreSQL): Añadir campos para MVP en tabla eventos_partido
-- Fecha: 2026-05-02
-- Descripción: Añade campos puntuacion_mvp e incidencias para registrar el MVP del partido
-- Nota: Versión compatible con PostgreSQL (la migración original usaba sintaxis MySQL)

-- Añadir campo para la puntuación del MVP (decimal con 2 dígitos)
ALTER TABLE eventos_partido
ADD COLUMN IF NOT EXISTS puntuacion_mvp DECIMAL(3,2) NULL;

-- Añadir campo para incidencias/notas del partido
ALTER TABLE eventos_partido
ADD COLUMN IF NOT EXISTS incidencias TEXT NULL;

-- Añadir comentarios a las columnas (sintaxis PostgreSQL)
COMMENT ON COLUMN eventos_partido.puntuacion_mvp IS 'Puntuación del MVP (0-10), solo para eventos tipo mvp';
COMMENT ON COLUMN eventos_partido.incidencias IS 'Notas o incidencias del partido, solo para eventos tipo mvp';

-- Verificar columnas añadidas (opcional)
-- \d eventos_partido
