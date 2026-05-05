-- ============================================================
-- SCRIPT DE ASIGNACION DE ROL ADMIN PARA TESTING
-- ============================================================
-- Propósito: Asignar rol de admin (id_rol=2) al usuario k@gmail.com (id=260)
--            en las ligas de testing (54, 55, 62, 63)
--
-- Uso: Ejecutar en Supabase SQL Editor o via psql
-- ============================================================

-- Verificar que el usuario existe
SELECT id_usuario, email, nombre FROM usuario WHERE id_usuario = 260;

-- Verificar que las ligas existen
SELECT id_liga, nombre FROM liga WHERE id_liga IN (54, 55, 62, 63);

-- Verificar el rol admin
SELECT id_rol, nombre FROM rol WHERE id_rol = 2;

-- ============================================================
-- ASIGNAR ROL ADMIN EN LAS 4 LIGAS DE TESTING
-- ============================================================

-- Liga 54: Delegado Test
INSERT INTO usuario_rol (id_usuario, id_rol, id_liga, activo)
SELECT 260, 2, 54, true
WHERE NOT EXISTS (
    SELECT 1 FROM usuario_rol WHERE id_usuario = 260 AND id_liga = 54
);

-- Liga 55: Jugador Test
INSERT INTO usuario_rol (id_usuario, id_rol, id_liga, activo)
SELECT 260, 2, 55, true
WHERE NOT EXISTS (
    SELECT 1 FROM usuario_rol WHERE id_usuario = 260 AND id_liga = 55
);

-- Liga 62: Viewer Test
INSERT INTO usuario_rol (id_usuario, id_rol, id_liga, activo)
SELECT 260, 2, 62, true
WHERE NOT EXISTS (
    SELECT 1 FROM usuario_rol WHERE id_usuario = 260 AND id_liga = 62
);

-- Liga 63: Entrenador Test
INSERT INTO usuario_rol (id_usuario, id_rol, id_liga, activo)
SELECT 260, 2, 63, true
WHERE NOT EXISTS (
    SELECT 1 FROM usuario_rol WHERE id_usuario = 260 AND id_liga = 63
);

-- ============================================================
-- VERIFICAR ASIGNACIONES CREADAS
-- ============================================================
SELECT
    ur.id_usuario_rol,
    u.nombre AS usuario,
    u.email,
    l.nombre AS liga,
    r.nombre AS rol,
    ur.activo
FROM usuario_rol ur
JOIN usuario u ON ur.id_usuario = u.id_usuario
JOIN liga l ON ur.id_liga = l.id_liga
JOIN rol r ON ur.id_rol = r.id_rol
WHERE ur.id_usuario = 260
  AND ur.id_liga IN (54, 55, 62, 63)
ORDER BY ur.id_liga;
