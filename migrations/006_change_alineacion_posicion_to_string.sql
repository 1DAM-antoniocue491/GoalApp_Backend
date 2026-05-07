-- Migración 006: Cambiar id_posicion en alineacion_partido de Integer a String
-- Fecha: 2026-05-08
-- Descripción: Cambia el tipo de dato de id_posicion para almacenar nombres de posición en lugar de IDs enteros
--              Esto previene valores inválidos y mantiene consistencia con la tabla jugadores

-- Para MySQL:
-- ALTER TABLE alineacion_partido MODIFY COLUMN id_posicion VARCHAR(50) NOT NULL;

-- Para PostgreSQL:
ALTER TABLE alineacion_partido ALTER COLUMN id_posicion TYPE VARCHAR(50);

-- Nota: Los valores existentes de id_posicion (enteros) se convertirán a string.
--       Se recomienda actualizar los datos existentes a nombres válidos:
--       1 -> 'portero'
--       2-5 -> 'defensa'
--       6-9 -> 'mediocentro' o 'centrocampista'
--       10-13 -> 'delantero'
--
-- Para actualizar datos existentes (opcional, ejecutar antes del ALTER si hay datos):
-- UPDATE alineacion_partido SET id_posicion =
--     CASE
--         WHEN id_posicion = 1 THEN 'portero'
--         WHEN id_posicion BETWEEN 2 AND 5 THEN 'defensa'
--         WHEN id_posicion BETWEEN 6 AND 9 THEN 'mediocentro'
--         WHEN id_posicion >= 10 THEN 'delantero'
--         ELSE 'desconocido'
--     END;
