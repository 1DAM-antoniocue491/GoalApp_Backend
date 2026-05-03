-- =============================================================================
-- SCRIPT DE ELIMINACIÓN DE DATOS - GoalApp
-- =============================================================================
-- ADVERTENCIA: Este script ELIMINA TODOS LOS DATOS de la base de datos.
--              Es una operación DESTRUCTIVA e IRREVERSIBLE.
--
-- Uso: Ejecutar solo en entornos de desarrollo/testing o cuando se requiera
--      un reset completo de la base de datos.
--
-- Base de datos: PostgreSQL (Supabase)
-- =============================================================================

-- Inicio de transacción para asegurar atomicidad
BEGIN;

-- =============================================================================
-- ORDEN DE ELIMINACIÓN: Tablas hijo → Tablas padre
-- =============================================================================
-- Este orden respeta las foreign key constraints eliminando primero
-- las tablas que dependen de otras.

-- ----------------------------------------------------------------------------
-- NIVEL 1: Tablas de eventos, estados y relaciones de partido
-- (Dependen de: partidos, jugadores)
-- ----------------------------------------------------------------------------
DELETE FROM evento_partido;
DELETE FROM estado_jugador_partido;
DELETE FROM alineacion_partido;
DELETE FROM convocatoria_partido;

-- ----------------------------------------------------------------------------
-- NIVEL 2: Tablas de competición (partidos y jornadas)
-- (Dependen de: ligas, equipos)
-- ----------------------------------------------------------------------------
DELETE FROM partidos;
DELETE FROM jornadas;

-- ----------------------------------------------------------------------------
-- NIVEL 3: Tablas de participantes (jugadores y equipos)
-- (Dependen de: ligas, usuarios)
-- ----------------------------------------------------------------------------
DELETE FROM jugadores;
DELETE FROM equipos;

-- ----------------------------------------------------------------------------
-- NIVEL 4: Tablas de configuración y seguimiento de ligas
-- (Dependen de: ligas, usuarios, roles)
-- ----------------------------------------------------------------------------
DELETE FROM liga_configuracion;
DELETE FROM usuario_sigue_liga;
DELETE FROM invitaciones;
DELETE FROM notificaciones;

-- ----------------------------------------------------------------------------
-- NIVEL 5: Tablas de asignación de roles por liga
-- (Dependen de: usuarios, roles, ligas)
-- ----------------------------------------------------------------------------
DELETE FROM usuario_rol;

-- ----------------------------------------------------------------------------
-- NIVEL 6: Tablas de autenticación (últimas por ser fundamentales)
-- (Dependen de: usuarios)
-- ----------------------------------------------------------------------------
DELETE FROM tokens_recuperacion;

-- ----------------------------------------------------------------------------
-- NIVEL 7: Tablas principales (usuarios, roles, ligas)
-- (Sin dependencias externas)
-- ----------------------------------------------------------------------------
DELETE FROM usuarios;
DELETE FROM roles;
DELETE FROM ligas;

-- =============================================================================
-- Confirmar transacción
-- =============================================================================
COMMIT;

-- =============================================================================
-- Verificación post-ejecución
-- =============================================================================
-- Ejecutar las siguientes consultas para verificar que las tablas están vacías:

SELECT 'usuarios' as tabla, COUNT(*) as filas FROM usuarios
UNION ALL SELECT 'roles', COUNT(*) FROM roles
UNION ALL SELECT 'ligas', COUNT(*) FROM ligas
UNION ALL SELECT 'equipos', COUNT(*) FROM equipos
UNION ALL SELECT 'jugadores', COUNT(*) FROM jugadores
UNION ALL SELECT 'partidos', COUNT(*) FROM partidos
UNION ALL SELECT 'jornadas', COUNT(*) FROM jornadas
UNION ALL SELECT 'evento_partido', COUNT(*) FROM evento_partido
UNION ALL SELECT 'convocatoria_partido', COUNT(*) FROM convocatoria_partido
UNION ALL SELECT 'alineacion_partido', COUNT(*) FROM alineacion_partido
UNION ALL SELECT 'estado_jugador_partido', COUNT(*) FROM estado_jugador_partido
UNION ALL SELECT 'usuario_rol', COUNT(*) FROM usuario_rol
UNION ALL SELECT 'invitaciones', COUNT(*) FROM invitaciones
UNION ALL SELECT 'notificaciones', COUNT(*) FROM notificaciones
UNION ALL SELECT 'tokens_recuperacion', COUNT(*) FROM tokens_recuperacion
UNION ALL SELECT 'liga_configuracion', COUNT(*) FROM liga_configuracion
UNION ALL SELECT 'usuario_sigue_liga', COUNT(*) FROM usuario_sigue_liga;
