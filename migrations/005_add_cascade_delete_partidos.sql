-- Migración: Añadir ON DELETE CASCADE a partidos.id_equipo_local y partidos.id_equipo_visitante
-- Propósito: Eliminar partidos automáticamente cuando se elimina un equipo (BUG 3.6)
-- Fecha: 2026-05-08

-- Eliminar foreign keys existentes y recrearlas con ON DELETE CASCADE
-- Para equipo_local
ALTER TABLE partidos
DROP CONSTRAINT IF EXISTS partidos_id_equipo_local_fkey;

ALTER TABLE partidos
ADD CONSTRAINT partidos_id_equipo_local_fkey
FOREIGN KEY (id_equipo_local) REFERENCES equipos(id_equipo) ON DELETE CASCADE;

-- Para equipo_visitante
ALTER TABLE partidos
DROP CONSTRAINT IF EXISTS partidos_id_equipo_visitante_fkey;

ALTER TABLE partidos
ADD CONSTRAINT partidos_id_equipo_visitante_fkey
FOREIGN KEY (id_equipo_visitante) REFERENCES equipos(id_equipo) ON DELETE CASCADE;

-- Nota: El cascade desde Equipo -> Partido ya está configurado en el modelo SQLAlchemy
-- con cascade="all, delete-orphan" en las relaciones equipo.partidos_local y equipo.partidos_visitante
-- Esta migración asegura que la base de datos también aplique el cascade a nivel de SQL
