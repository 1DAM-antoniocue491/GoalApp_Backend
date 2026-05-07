-- Migración: Añadir ON DELETE CASCADE a jugadores.id_usuario
-- Propósito: Evitar jugadores huérfanos cuando se elimina un usuario
-- Fecha: 2026-05-08

-- Eliminar la foreign key existente y recrearla con ON DELETE CASCADE
ALTER TABLE jugadores
DROP CONSTRAINT IF EXISTS jugadores_id_usuario_fkey;

ALTER TABLE jugadores
ADD CONSTRAINT jugadores_id_usuario_fkey
FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE;

-- Nota: El cascade desde Usuario -> Jugador también está configurado en el modelo SQLAlchemy
-- con cascade="all, delete-orphan" en la relación usuario.jugador
