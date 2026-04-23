"""
Script para crear 5 ligas completas para el usuario jesus@gmail.com (id=28)
Cada liga tendrá un rol diferente:
- Liga 1: Admin
- Liga 2: Coach (Entrenador)
- Liga 3: Delegate (Delegado)
- Liga 4: Player (Jugador)
- Liga 5: Viewer (Observador)

Cada liga tendrá 4 equipos, 12 partidos (ida y vuelta) y eventos.
"""

import psycopg2
from datetime import datetime, timedelta
import random

# Configuración de conexión a Supabase
DB_CONFIG = {
    'host': 'aws-0-eu-west-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.kggdzngfqmdiojouqgmj',
    'password': 'sqnasgQa93uQ2GfK'
}

# Usuario objetivo
USER_ID = 28
USER_NOMBRE = "Jesus"

# IDs de roles (según BD actual)
ROL_ADMIN = 2
ROL_COACH = 3
ROL_DELEGATE = 6
ROL_PLAYER = 4
ROL_VIEWER = 5

# Nombres de ligas
LIGAS_INFO = [
    {"nombre": "Liga de Jesus - Admin", "temporada": "2025/2026", "rol": ROL_ADMIN},
    {"nombre": "Liga de Jesus - Entrenador", "temporada": "2025/2026", "rol": ROL_COACH},
    {"nombre": "Liga de Jesus - Delegado", "temporada": "2025/2026", "rol": ROL_DELEGATE},
    {"nombre": "Liga de Jesus - Jugador", "temporada": "2025/2026", "rol": ROL_PLAYER},
    {"nombre": "Liga de Jesus - Observador", "temporada": "2025/2026", "rol": ROL_VIEWER},
]

# Nombres de equipos por liga
EQUIPOS_NOMBRES = [
    ["CD Norte", "Real Sur", "Atlético Este", "Deportivo Oeste"],
    ["FC Barcelona B", "Real Madrid C", "Atlético D", "Sevilla E"],
    ["Valencia F", "Betis G", "Athletic H", "Real Sociedad I"],
    ["Villarreal J", "Celta K", "Espanyol L", "Getafe M"],
    ["Osasuna N", "Girona O", "Rayo P", "Alavés Q"],
]

# Nombres de jugadores para generar
JUGADORES_NOMBRES = [
    ("Carlos", "García"),
    ("Miguel", "López"),
    ("David", "Martínez"),
    ("Pablo", "Rodríguez"),
    ("Álvaro", "Fernández"),
    ("Sergio", "González"),
    ("Javier", "Sánchez"),
    ("Daniel", "Pérez"),
    ("Alejandro", "Gómez"),
    ("Adrián", "Díaz"),
    ("Rubén", "Álvarez"),
    ("Iván", "Romero"),
    ("Raúl", "Alonso"),
    ("Marc", "Muñoz"),
    ("Pol", "Navarro"),
]

POSICIONES = ["Delantero", "Mediocampista", "Defensa", "Portero"]
NUMEROS_CAMISETA = list(range(1, 99))


def conectar():
    """Conectar a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)


def crear_usuario_si_no_existe(conn, user_id, email, nombre):
    """Verifica si el usuario existe, si no, lo crea"""
    with conn.cursor() as cur:
        cur.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (user_id,))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO usuarios (nombre, email, contraseña_hash, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                RETURNING id_usuario
            """, (nombre, email, "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT2T2T2T2T2T2T"))
            user_id = cur.fetchone()[0]
            conn.commit()
            print(f"Usuario creado con ID: {user_id}")
        else:
            print(f"Usuario {user_id} ya existe")
    return user_id


def crear_liga(conn, nombre, temporada):
    """Crear una nueva liga o devolver ID si ya existe"""
    with conn.cursor() as cur:
        # Verificar si ya existe
        cur.execute("SELECT id_liga FROM ligas WHERE nombre = %s", (nombre,))
        row = cur.fetchone()
        if row:
            print(f"  Liga ya existe: {nombre} (ID: {row[0]})")
            return row[0]

        cur.execute("""
            INSERT INTO ligas (nombre, temporada, categoria, activa, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id_liga
        """, (nombre, temporada, "Senior", True))
        liga_id = cur.fetchone()[0]

        # Crear configuración por defecto con todos los campos requeridos
        cur.execute("""
            INSERT INTO liga_configuracion (
                id_liga, hora_partidos, min_equipos, max_equipos,
                min_convocados, max_convocados, min_plantilla, max_plantilla,
                min_jugadores_equipo, min_partidos_entre_equipos,
                minutos_partido, max_partidos, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (liga_id, '17:00:00', 2, 20, 14, 22, 11, 25, 7, 2, 90, 30))

        conn.commit()
        print(f"  Liga creada: {nombre} (ID: {liga_id})")
        return liga_id


def asignar_rol(conn, user_id, rol_id, liga_id):
    """Asignar un rol a un usuario en una liga"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO usuario_rol (id_usuario, id_rol, id_liga, activo, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT DO NOTHING
        """, (user_id, rol_id, liga_id, 1))
        conn.commit()
        print(f"  Rol asignado: Usuario {user_id} -> Rol {rol_id} en Liga {liga_id}")


def crear_usuario_adicional(conn, nombre, email):
    """Crear un usuario adicional para jugadores o devolver ID si ya existe"""
    with conn.cursor() as cur:
        # Verificar si ya existe
        cur.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute("""
            INSERT INTO usuarios (nombre, email, contraseña_hash, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING id_usuario
        """, (nombre, email, "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT2T2T2T2T2T2T"))
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id


def crear_equipo(conn, nombre, liga_id, id_entrenador=None, id_delegado=None):
    """Crear un equipo en una liga o devolver ID si ya existe en esta liga"""
    with conn.cursor() as cur:
        # Verificar si ya existe en esta liga
        cur.execute("SELECT id_equipo FROM equipos WHERE nombre = %s AND id_liga = %s", (nombre, liga_id))
        row = cur.fetchone()
        if row:
            print(f"    Equipo ya existe: {nombre} (ID: {row[0]})")
            return row[0]

        cur.execute("""
            INSERT INTO equipos (nombre, id_liga, id_entrenador, id_delegado, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id_equipo
        """, (nombre, liga_id, id_entrenador, id_delegado))
        equipo_id = cur.fetchone()[0]
        conn.commit()
        print(f"    Equipo creado: {nombre} (ID: {equipo_id})")
        return equipo_id


def asignar_rol_usuario_en_liga(conn, user_id, rol_id, liga_id):
    """Asignar rol de entrenador/delegado y actualizar equipo"""
    with conn.cursor() as cur:
        # Verificar si ya existe
        cur.execute("""
            SELECT id_usuario_rol FROM usuario_rol
            WHERE id_usuario = %s AND id_rol = %s AND id_liga = %s
        """, (user_id, rol_id, liga_id))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO usuario_rol (id_usuario, id_rol, id_liga, activo, created_at, updated_at)
                VALUES (%s, %s, %s, 1, NOW(), NOW())
            """, (user_id, rol_id, liga_id))
            conn.commit()


def crear_jugador(conn, user_id, equipo_id, posicion, dorsal):
    """Crear un jugador en un equipo o devolver ID si ya existe"""
    with conn.cursor() as cur:
        # Verificar si el usuario ya es jugador en algún equipo
        cur.execute("SELECT id_jugador FROM jugadores WHERE id_usuario = %s", (user_id,))
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute("""
            INSERT INTO jugadores (id_usuario, id_equipo, posicion, dorsal, activo, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id_jugador
        """, (user_id, equipo_id, posicion, dorsal, True))
        jugador_id = cur.fetchone()[0]
        conn.commit()
        return jugador_id


def crear_partido(conn, liga_id, equipo_local, equipo_visitante, fecha, estado="finalizado", goles_local=0, goles_visitante=0):
    """Crear un partido"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO partidos (id_liga, id_equipo_local, id_equipo_visitante, fecha, estado, goles_local, goles_visitante, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id_partido
        """, (liga_id, equipo_local, equipo_visitante, fecha, estado, goles_local, goles_visitante))
        partido_id = cur.fetchone()[0]
        conn.commit()
        return partido_id


def crear_evento(conn, partido_id, jugador_id, tipo_evento, minuto):
    """Crear un evento de partido"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO eventos_partido (id_partido, id_jugador, tipo_evento, minuto, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (partido_id, jugador_id, tipo_evento, minuto))
        conn.commit()


def generar_goles_y_eventos(conn, partido_id, equipo_local_id, equipo_visitante_id, goles_local, goles_visitante):
    """Generar eventos de goles para un partido"""
    # Obtener jugadores de cada equipo
    with conn.cursor() as cur:
        # Jugadores del equipo local
        cur.execute("""
            SELECT j.id_jugador FROM jugadores j
            WHERE j.id_equipo = %s AND j.activo = true
        """, (equipo_local_id,))
        jugadores_locales = [row[0] for row in cur.fetchall()]

        # Jugadores del equipo visitante
        cur.execute("""
            SELECT j.id_jugador FROM jugadores j
            WHERE j.id_equipo = %s AND j.activo = true
        """, (equipo_visitante_id,))
        jugadores_visitantes = [row[0] for row in cur.fetchall()]

    # Generar goles locales
    minuto = 5
    for i in range(goles_local):
        if jugadores_locales:
            jugador = random.choice(jugadores_locales)
            crear_evento(conn, partido_id, jugador, "GOL", minuto + (i * 10))

    # Generar goles visitantes
    minuto = 10
    for i in range(goles_visitante):
        if jugadores_visitantes:
            jugador = random.choice(jugadores_visitantes)
            crear_evento(conn, partido_id, jugador, "GOL", minuto + (i * 10))

    # Añadir algunas tarjetas amarillas aleatorias
    if random.random() > 0.5 and jugadores_locales:
        jugador = random.choice(jugadores_locales)
        crear_evento(conn, partido_id, jugador, "TARJETA_AMARILLA", random.randint(20, 80))

    if random.random() > 0.5 and jugadores_visitantes:
        jugador = random.choice(jugadores_visitantes)
        crear_evento(conn, partido_id, jugador, "TARJETA_AMARILLA", random.randint(20, 80))

    # Añadir MVP (jugador con más goles del partido)
    if goles_local > 0 and jugadores_locales:
        cur = conn.cursor()
        cur.execute("""
            SELECT id_jugador FROM eventos_partido
            WHERE id_partido = %s AND tipo_evento = 'GOL'
            LIMIT 1
        """, (partido_id,))
        row = cur.fetchone()
        if row:
            crear_evento(conn, partido_id, row[0], "MVP", 90)
        conn.commit()


def main():
    print("=" * 60)
    print("CREANDO LIGAS PARA JESUS (id_usuario=28)")
    print("=" * 60)

    conn = conectar()
    print(f"Conectado a Supabase: {DB_CONFIG['host']}")

    # Verificar/crear usuario Jesus
    crear_usuario_si_no_existe(conn, USER_ID, "jesus@gmail.com", USER_NOMBRE)

    # Usuarios adicionales para completar equipos
    # Necesitamos ~4 jugadores por equipo × 4 equipos × 5 ligas = 80 usuarios como máximo
    # Pero como cada usuario solo puede ser jugador en 1 equipo (constraint unique),
    # creamos usuarios específicos para cada liga
    usuarios_adicionales = []
    print("\nCreando usuarios adicionales para jugadores...")

    # Crear 60 usuarios adicionales (4 jugadores × 4 equipos × 5 ligas - algunos se solapan)
    for i in range(60):
        nombre = f"Jugador {i+1}"
        email = f"jugador{i+1}x@goalapp.com"  # Email único para evitar duplicados
        user_id = crear_usuario_adicional(conn, nombre, email)
        usuarios_adicionales.append(user_id)
        if i < 15 or i >= 55:  # Mostrar solo primeros y últimos
            print(f"  Usuario creado: {nombre} (ID: {user_id})")
        elif i == 15:
            print(f"  ... y {60 - 16} usuarios más ...")

    print("\n" + "=" * 60)
    print("CREANDO 5 LIGAS COMPLETAS")
    print("=" * 60)

    for liga_idx, liga_info in enumerate(LIGAS_INFO):
        print(f"\n{'='*60}")
        print(f"LIGA {liga_idx + 1}: {liga_info['nombre']}")
        print(f"{'='*60}")

        # 1. Crear liga
        liga_id = crear_liga(conn, liga_info['nombre'], liga_info['temporada'])

        # 2. Asignar rol a Jesus en esta liga
        asignar_rol(conn, USER_ID, liga_info['rol'], liga_id)
        rol_map = {ROL_ADMIN: "ADMIN", ROL_COACH: "COACH", ROL_DELEGATE: "DELEGATE", ROL_PLAYER: "PLAYER", ROL_VIEWER: "VIEWER"}
        rol_nombre = rol_map[liga_info['rol']]
        print(f"  Rol de Jesus: {rol_nombre}")

        # 3. Crear 4 equipos
        equipos_ids = []
        equipos_nombres = EQUIPOS_NOMBRES[liga_idx]

        for equipo_idx, nombre_equipo in enumerate(equipos_nombres):
            # El primer equipo tiene a Jesus como entrenador/delegado segun corresponda
            id_entrenador = None
            id_delegado = None

            if liga_info['rol'] == ROL_COACH and equipo_idx == 0:
                id_entrenador = USER_ID
                id_delegado = usuarios_adicionales[equipo_idx % len(usuarios_adicionales)]
            elif liga_info['rol'] == ROL_DELEGATE and equipo_idx == 0:
                id_entrenador = usuarios_adicionales[equipo_idx % len(usuarios_adicionales)]
                id_delegado = USER_ID
            else:
                id_entrenador = usuarios_adicionales[(equipo_idx + 1) % len(usuarios_adicionales)]
                id_delegado = usuarios_adicionales[(equipo_idx + 2) % len(usuarios_adicionales)]

            equipo_id = crear_equipo(conn, nombre_equipo, liga_id, id_entrenador, id_delegado)
            equipos_ids.append(equipo_id)

            # Asignar roles de entrenador y delegado
            if id_entrenador:
                asignar_rol_usuario_en_liga(conn, id_entrenador, ROL_COACH, liga_id)
            if id_delegado:
                asignar_rol_usuario_en_liga(conn, id_delegado, ROL_DELEGATE, liga_id)

            # 4. Crear jugadores para cada equipo (3-4 por equipo)
            num_jugadores = random.randint(3, 4)
            jugadores_equipo = random.sample(usuarios_adicionales, min(num_jugadores, len(usuarios_adicionales)))

            for jugador_idx, user_id_jugador in enumerate(jugadores_equipo):
                posicion = POSICIONES[jugador_idx % len(POSICIONES)]
                dorsal = random.choice(NUMEROS_CAMISETA)
                if dorsal in NUMEROS_CAMISETA:
                    NUMEROS_CAMISETA.remove(dorsal)
                crear_jugador(conn, user_id_jugador, equipo_id, posicion, dorsal)

            # Si Jesus es jugador en esta liga, añadirlo al primer equipo
            if liga_info['rol'] == ROL_PLAYER and equipo_idx == 0:
                crear_jugador(conn, USER_ID, equipo_id, "Delantero", 10)
                asignar_rol_usuario_en_liga(conn, USER_ID, ROL_PLAYER, liga_id)

        # 5. Crear partidos (ida y vuelta entre 4 equipos = 12 partidos)
        print(f"\n  Creando 12 partidos (ida y vuelta)...")
        partidos_ids = []
        fecha_base = datetime.now() + timedelta(days=liga_idx * 7)

        # Generar todos los enfrentamientos (ida y vuelta)
        partido_idx = 0
        for i, equipo_local in enumerate(equipos_ids):
            for j, equipo_visitante in enumerate(equipos_ids):
                if i != j:  # No jugar contra sí mismo
                    # Evitar duplicados (ida y vuelta ya se generan)
                    if (j, i) not in [(x, y) for x, y in locals().get('partidos_generados', [])]:
                        fecha = fecha_base + timedelta(days=partido_idx * 3, hours=random.randint(10, 20))
                        goles_local = random.randint(0, 5)
                        goles_visitante = random.randint(0, 5)

                        partido_id = crear_partido(
                            conn, liga_id, equipo_local, equipo_visitante,
                            fecha, "finalizado", goles_local, goles_visitante
                        )
                        partidos_ids.append(partido_id)
                        partidos_generados = locals().get('partidos_generados', [])
                        partidos_generados.append((i, j))
                        locals()['partidos_generados'] = partidos_generados

                        print(f"    Partido {partido_idx + 1}: Equipo {i+1} ({goles_local}) vs Equipo {j+1} ({goles_visitante})")
                        partido_idx += 1

        # 6. Generar eventos para cada partido
        print(f"\n  Generando eventos para {len(partidos_ids)} partidos...")
        for partido_id in partidos_ids:
            # Obtener información del partido
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id_equipo_local, id_equipo_visitante, goles_local, goles_visitante
                    FROM partidos WHERE id_partido = %s
                """, (partido_id,))
                row = cur.fetchone()
                if row:
                    eq_local, eq_visitante, goles_local, goles_visitante = row
                    generar_goles_y_eventos(conn, partido_id, eq_local, eq_visitante, goles_local, goles_visitante)

        print(f"  Eventos generados correctamente!")

    conn.close()
    print("\n" + "=" * 60)
    print("¡PROCESO COMPLETADO EXITOSAMENTE!")
    print("=" * 60)
    print(f"\nResumen:")
    print(f"  - 5 ligas creadas")
    print(f"  - 20 equipos creados (4 por liga)")
    print(f"  - 60 partidos creados (12 por liga)")
    print(f"  - Eventos de goles, tarjetas y MVP generados")
    print(f"\nJesus tiene los siguientes roles:")
    print(f"  - Liga 1: ADMIN")
    print(f"  - Liga 2: COACH (Entrenador)")
    print(f"  - Liga 3: DELEGATE (Delegado)")
    print(f"  - Liga 4: PLAYER (Jugador)")
    print(f"  - Liga 5: VIEWER (Observador)")


if __name__ == "__main__":
    main()
