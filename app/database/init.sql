-- Tablas independientes (sin foreign keys)
-- Compatible con PostgreSQL

CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    contraseña_hash VARCHAR(255) NOT NULL,
    genero VARCHAR(50) NULL CHECK (genero IN ('masculino', 'femenino', 'otro')),
    telefono VARCHAR(20) NULL,
    fecha_nacimiento DATE NULL,
    imagen_url VARCHAR(255) NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL
);

CREATE TABLE roles (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL
);

CREATE TABLE ligas (
    id_liga SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    temporada VARCHAR(20) NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL
);

CREATE TABLE posicion_formacion (
    id_posicion SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL
);

-- Tablas con foreign keys a tablas independientes

CREATE TABLE usuario_rol (
    id_usuario_rol SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_rol INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol) ON DELETE CASCADE
);

CREATE TABLE usuario_sigue_liga (
    id_seguimiento SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_liga INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_liga) REFERENCES ligas(id_liga) ON DELETE CASCADE,
    CONSTRAINT unique_usuario_liga UNIQUE (id_usuario, id_liga)
);

CREATE TABLE liga_configuracion (
    id_configuracion SERIAL PRIMARY KEY,
    id_liga INT NOT NULL UNIQUE,
    hora_partidos TIME NOT NULL DEFAULT '17:00:00',
    max_equipos INT NOT NULL DEFAULT 20,
    min_jugadores_equipo INT NOT NULL DEFAULT 7,
    min_partidos_entre_equipos INT NOT NULL DEFAULT 2,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_liga) REFERENCES ligas(id_liga) ON DELETE CASCADE
);

CREATE TABLE equipos (
    id_equipo SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ciudad VARCHAR(255),
    escudo VARCHAR(255),
    colores VARCHAR(50),
    id_liga INT NOT NULL,
    id_entrenador INT NOT NULL,
    id_delegado INT NOT NULL,
    estadio VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_liga) REFERENCES ligas(id_liga),
    FOREIGN KEY (id_entrenador) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_delegado) REFERENCES usuarios(id_usuario)
);

CREATE TABLE jugadores (
    id_jugador SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_equipo INT NOT NULL,
    posicion VARCHAR(50) NOT NULL,
    dorsal INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo)
);

CREATE TABLE partidos (
    id_partido SERIAL PRIMARY KEY,
    id_liga INT NOT NULL,
    id_equipo_local INT NOT NULL,
    id_equipo_visitante INT NOT NULL,
    fecha TIMESTAMPTZ NOT NULL,
    estado VARCHAR(50) NOT NULL CHECK (estado IN ('programado', 'en_juego', 'finalizado', 'cancelado')),
    goles_local INT,
    goles_visitante INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_liga) REFERENCES ligas(id_liga),
    FOREIGN KEY (id_equipo_local) REFERENCES equipos(id_equipo),
    FOREIGN KEY (id_equipo_visitante) REFERENCES equipos(id_equipo)
);

CREATE TABLE evento_partido (
    id_evento SERIAL PRIMARY KEY,
    id_partido INT NOT NULL,
    id_jugador INT NOT NULL,
    tipo_evento VARCHAR(50) NOT NULL CHECK (tipo_evento IN ('gol', 'tarjeta_amarilla', 'tarjeta_roja', 'cambio', 'mvp')),
    minuto INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id_jugador)
);

CREATE TABLE alineacion_partido (
    id_alineacion SERIAL PRIMARY KEY,
    id_partido INT NOT NULL,
    id_jugador INT NOT NULL,
    id_posicion INT NOT NULL,
    titular BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id_jugador),
    FOREIGN KEY (id_posicion) REFERENCES posicion_formacion(id_posicion)
);

CREATE TABLE notificaciones (
    id_notificacion SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE convocatoria_partido (
    id_convocatoria SERIAL PRIMARY KEY,
    id_partido INT NOT NULL,
    id_jugador INT NOT NULL,
    es_titular BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (id_partido) REFERENCES partidos(id_partido) ON DELETE CASCADE,
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id_jugador) ON DELETE CASCADE,
    CONSTRAINT unique_jugador_partido UNIQUE (id_jugador, id_partido)
);

CREATE TABLE tokens_recuperacion (
    id_token SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    fecha_expiracion TIMESTAMPTZ NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- Datos iniciales

INSERT INTO roles (nombre, descripcion) VALUES
    ('admin', 'Administrador del sistema con acceso total'),
    ('coach', 'Entrenador de equipo'),
    ('player', 'Jugador'),
    ('viewer', 'Visualizador de información pública'),
    ('delegate', 'Delegado de equipo');