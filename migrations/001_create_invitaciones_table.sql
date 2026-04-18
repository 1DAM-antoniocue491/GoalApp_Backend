-- Migración: Tabla invitaciones
-- Fecha: 2026-04-18
-- Descripción: Crea la tabla para gestionar invitaciones a ligas por email

CREATE TABLE IF NOT EXISTS invitaciones (
    id_invitacion INT AUTO_INCREMENT PRIMARY KEY,

    -- Token y email
    token VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL,

    -- Relaciones
    id_liga INT NOT NULL,
    id_equipo INT NULL,
    id_rol INT NOT NULL,

    -- Detalles de la invitación
    dorsal VARCHAR(10) NULL,
    posicion VARCHAR(50) NULL,
    tipo_jugador VARCHAR(50) NULL,

    -- Usuario que invita (admin de la liga)
    invitado_por INT NOT NULL,

    -- Estado y expiración
    fecha_expiracion DATETIME NOT NULL,
    usada BOOLEAN NOT NULL DEFAULT FALSE,

    -- Auditoría
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Índices para búsquedas rápidas
    INDEX idx_token (token),
    INDEX idx_email (email),
    INDEX idx_usada (usada),

    -- Claves foráneas
    CONSTRAINT fk_invitacion_liga FOREIGN KEY (id_liga) REFERENCES ligas(id_liga) ON DELETE CASCADE,
    CONSTRAINT fk_invitacion_equipo FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo) ON DELETE SET NULL,
    CONSTRAINT fk_invitacion_rol FOREIGN KEY (id_rol) REFERENCES roles(id_rol) ON DELETE RESTRICT,
    CONSTRAINT fk_invitacion_usuario FOREIGN KEY (invitado_por) REFERENCES usuarios(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Nota: Esta tabla se crea automáticamente al iniciar el backend
-- gracias a que el modelo Invitacion está registrado en main.py.
-- Este SQL es solo para referencia o para crear manualmente si es necesario.
