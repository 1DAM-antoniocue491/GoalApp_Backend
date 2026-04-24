-- Migración 003: Añadir campos para MVP en tabla eventos_partido
-- Fecha: 2026-04-24
-- Descripción: Añade campos puntuacion_mvp e incidencias para registrar el MVP del partido

-- Añadir campo para la puntuación del MVP (decimal con 2 dígitos)
ALTER TABLE eventos_partido
ADD COLUMN puntuacion_mvp DECIMAL(3,2) NULL COMMENT 'Puntuación del MVP (0-10), solo para eventos tipo mvp';

-- Añadir campo para incidencias/notas del partido
ALTER TABLE eventos_partido
ADD COLUMN incidencias TEXT NULL COMMENT 'Notas o incidencias del partido, solo para eventos tipo mvp';

-- Verificar columnas añadidas
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'eventos_partido' AND COLUMN_NAME IN ('puntuacion_mvp', 'incidencias');
