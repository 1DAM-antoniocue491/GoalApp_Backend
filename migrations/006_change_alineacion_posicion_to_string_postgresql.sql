-- Migración 006: Cambiar id_posicion en alineacion_partido de Integer a String (PostgreSQL)
-- Fecha: 2026-05-08
-- Descripción: Cambia el tipo de dato de id_posicion para almacenar nombres de posición en lugar de IDs enteros
--              Esto previene valores inválidos y mantiene consistencia con la tabla jugadores

-- Primero, convertir valores enteros existentes a nombres válidos (si hay datos)
-- Ejecutar esto SOLO si la tabla ya tiene datos con valores enteros
UPDATE alineacion_partido
SET id_posicion = CASE
    WHEN id_posicion::INTEGER = 1 THEN 'portero'
    WHEN id_posicion::INTEGER BETWEEN 2 AND 5 THEN 'defensa'
    WHEN id_posicion::INTEGER BETWEEN 6 AND 9 THEN 'mediocentro'
    WHEN id_posicion::INTEGER >= 10 THEN 'delantero'
    ELSE 'desconocido'
END
WHERE id_posicion ~ '^[0-9]+$';

-- Cambiar el tipo de columna de INTEGER a VARCHAR(50)
ALTER TABLE alineacion_partido ALTER COLUMN id_posicion TYPE VARCHAR(50);

-- Añadir constraint CHECK para validar que solo se permitan posiciones válidas
ALTER TABLE alineacion_partido
ADD CONSTRAINT chk_posicion_valida
CHECK (LOWER(id_posicion) IN ('portero', 'defensa', 'mediocentro', 'centrocampista', 'delantero'));
