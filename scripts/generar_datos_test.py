"""
Script para generar datos de prueba para las ligas de test de k@gmail.com
"""
import requests
import random
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:8000/api/v1'

# Credenciales
USERNAME = 'k@gmail.com'
PASSWORD = 'k12345'

def login():
    """Autenticar y obtener token"""
    response = requests.post(f'{BASE_URL}/auth/login', data={
        'username': USERNAME,
        'password': PASSWORD
    })
    response.raise_for_status()
    return response.json()['access_token']

def obtener_ligas(headers):
    """Obtener ligas del usuario autenticado"""
    response = requests.get(f'{BASE_URL}/usuarios/me/ligas', headers=headers)
    response.raise_for_status()
    return response.json()

def crear_usuario(email, password, nombre, rol, headers):
    """Crear un nuevo usuario"""
    data = {
        'email': email,
        'password': password,
        'nombre': nombre,
        'rol_principal': rol
    }
    try:
        response = requests.post(f'{BASE_URL}/usuarios/', json=data, headers=headers)
        if response.status_code == 400:
            # Usuario ya existe, intentar obtener su ID
            return None, f'Usuario {email} ya existe'
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

def crear_equipo(nombre, id_liga, colores, headers):
    """Crear un nuevo equipo"""
    data = {
        'nombre': nombre,
        'id_liga': id_liga,
        'colores': colores,
        'escudo': ''
    }
    try:
        response = requests.post(f'{BASE_URL}/equipos/', json=data, headers=headers)
        if response.status_code == 400:
            return None, f'Equipo {nombre} ya existe'
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

def crear_jugador(id_usuario, id_equipo, dorsal, posicion, headers):
    """Crear un nuevo jugador"""
    data = {
        'id_usuario': id_usuario,
        'id_equipo': id_equipo,
        'dorsal': dorsal,
        'posicion': posicion,
        'activo': True
    }
    try:
        response = requests.post(f'{BASE_URL}/jugadores/', json=data, headers=headers)
        if response.status_code == 400:
            return None, f'Jugador usuario {id_usuario} equipo {id_equipo} ya existe'
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

def crear_partido(id_liga, id_local, id_visitante, fecha, estado, headers):
    """Crear un nuevo partido"""
    data = {
        'id_liga': id_liga,
        'id_equipo_local': id_local,
        'id_equipo_visitante': id_visitante,
        'fecha': fecha,
        'estado': estado
    }
    try:
        response = requests.post(f'{BASE_URL}/partidos/', json=data, headers=headers)
        if response.status_code == 400:
            return None, f'Partido ya existe'
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

def crear_evento(id_partido, id_jugador, tipo_evento, minuto, headers):
    """Crear un nuevo evento de partido"""
    data = {
        'id_partido': id_partido,
        'id_jugador': id_jugador,
        'tipo_evento': tipo_evento,
        'minuto': minuto
    }
    try:
        response = requests.post(f'{BASE_URL}/eventos/', json=data, headers=headers)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)

def obtener_jugadores_por_equipo(id_equipo, headers):
    """Obtener jugadores de un equipo"""
    response = requests.get(f'{BASE_URL}/equipos/{id_equipo}/jugadores', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def obtener_partidos_por_liga(id_liga, headers):
    """Obtener partidos de una liga"""
    response = requests.get(f'{BASE_URL}/ligas/{id_liga}/partidos', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def generar_datos_liga(liga, headers):
    """Generar todos los datos para una liga"""
    id_liga = liga['id']
    nombre_liga = liga['nombre']
    sufijo = f".liga{id_liga}"

    print(f"\n{'='*60}")
    print(f"Generando datos para liga: {nombre_liga} (ID: {id_liga})")
    print(f"{'='*60}")

    resumen = {
        'liga': nombre_liga,
        'id_liga': id_liga,
        'equipos': 0,
        'usuarios': 0,
        'jugadores': 0,
        'partidos': 0,
        'eventos': 0
    }

    # 1. Crear equipos (4-6 por liga)
    num_equipos = random.randint(4, 6)
    letras_equipo = ['A', 'B', 'C', 'D', 'E', 'F']
    colores = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']

    equipos = []
    print(f"\nCreando {num_equipos} equipos...")
    for i in range(num_equipos):
        nombre_equipo = f"Equipo {letras_equipo[i]}"
        equipo, error = crear_equipo(nombre_equipo, id_liga, colores[i], headers)
        if equipo:
            equipos.append(equipo)
            print(f"  ✓ Equipo {letras_equipo[i]} (ID: {equipo['id']})")
        elif error and 'ya existe' in error:
            print(f"  ~ Equipo {letras_equipo[i]} ya existe, buscando...")
            # Buscar equipos existentes de esta liga
            response = requests.get(f'{BASE_URL}/ligas/{id_liga}/equipos', headers=headers)
            if response.status_code == 200:
                equipos_liga = response.json()
                equipos = [e for e in equipos_liga if e['nombre'] == nombre_equipo]
                if equipos:
                    print(f"  ~ Usando equipo existente: {equipos[0]['nombre']} (ID: {equipos[0]['id']})")
        else:
            print(f"  ✗ Error creando equipo {letras_equipo[i]}: {error}")

    if not equipos:
        print("  ! No se pudieron crear equipos, saltando liga")
        return resumen

    resumen['equipos'] = len(equipos)

    # 2. Crear usuarios (coach + delegado por liga + 13 jugadores por equipo)
    usuarios_creados = {}  # email -> id_usuario

    # Delegado (uno por liga)
    email_delegado = f"delegado{sufijo}@test.com"
    usuario, error = crear_usuario(
        email_delegado,
        'delegado123',
        f'Delegado Liga {id_liga}',
        'delegado',
        headers
    )
    if usuario:
        usuarios_creados[email_delegado] = usuario['id']
        resumen['usuarios'] += 1
        print(f"  ✓ Delegado creado (ID: {usuario['id']})")
    else:
        print(f"  ~ Delegado: {error or 'ya existe'}")

    # Por cada equipo, crear coach y 13 jugadores
    posiciones = {
        1: 'portero',
        2: 'defensa', 3: 'defensa', 4: 'defensa', 5: 'defensa',
        6: 'centrocampista', 7: 'centrocampista', 8: 'centrocampista', 9: 'centrocampista',
        10: 'delantero', 11: 'delantero', 12: 'delantero', 13: 'delantero'
    }

    jugadores_por_equipo = {}  # id_equipo -> [jugadores]

    for equipo in equipos:
        id_equipo = equipo['id']
        letra = equipo['nombre'].split()[-1]  # A, B, C...
        jugadores_equipo = []

        # Coach del equipo
        email_coach = f"coach.equipo{letra.lower()}{sufijo}@test.com"
        usuario, error = crear_usuario(
            email_coach,
            'coach123',
            f'Coach Equipo {letra} Liga {id_liga}',
            'coach',
            headers
        )
        if usuario:
            usuarios_creados[email_coach] = usuario['id']
            resumen['usuarios'] += 1
            print(f"  ✓ Coach Equipo {letra} creado (ID: {usuario['id']})")
        else:
            print(f"  ~ Coach Equipo {letra}: {error or 'ya existe'}")

        # 13 jugadores por equipo
        print(f"  Creando 13 jugadores para Equipo {letra}...")
        for dorsal in range(1, 14):
            email_jugador = f"jugador{dorsal}.equipo{letra.lower()}{sufijo}@test.com"
            nombre_jugador = f"Jugador {dorsal} Equipo {letra} Liga {id_liga}"
            posicion = posiciones[dorsal]

            usuario, error = crear_usuario(
                email_jugador,
                'jugador123',
                nombre_jugador,
                'jugador',
                headers
            )

            if usuario:
                usuarios_creados[email_jugador] = usuario['id']
                resumen['usuarios'] += 1

                # Crear jugador vinculado al equipo
                jugador, error_j = crear_jugador(
                    usuario['id'],
                    id_equipo,
                    dorsal,
                    posicion,
                    headers
                )
                if jugador:
                    jugadores_equipo.append(jugador)
                    resumen['jugadores'] += 1
                    if dorsal <= 3:  # Solo mostrar primeros 3 para no saturar
                        print(f"    ✓ Jugador {dorsal} ({posicion}) - ID: {jugador['id']}")
                    elif dorsal == 4:
                        print(f"    ... y {10} más")
                else:
                    print(f"    ✗ Error jugador {dorsal}: {error_j}")
            else:
                print(f"    ~ Jugador {dorsal}: {error or 'ya existe'}")

        jugadores_por_equipo[id_equipo] = jugadores_equipo

    # 3. Crear partidos (10-15 por liga)
    print(f"\nCreando partidos...")
    num_partidos = random.randint(10, 15)
    partidos_creados = []

    # Generar enfrentamientos round-robin
    enfrentamientos = []
    for i, eq1 in enumerate(equipos):
        for j, eq2 in enumerate(equipos):
            if i < j:  # Cada par juega una vez
                enfrentamientos.append((eq1, eq2))

    # Si necesitamos más partidos, añadir vuelta
    if num_partidos > len(enfrentamientos):
        for i, eq1 in enumerate(equipos):
            for j, eq2 in enumerate(equipos):
                if i > j:  # Vuelta
                    enfrentamientos.append((eq1, eq2))

    # Limitar al número deseado
    enfrentamientos = enfrentamientos[:num_partidos]

    # Distribuir estados: 4 finalizados, 2 en_juego, resto programado
    base_date = datetime.now()

    for idx, (eq1, eq2) in enumerate(enfrentamientos):
        if idx < 4:
            estado = 'finalizado'
            fecha = (base_date - timedelta(days=random.randint(1, 10))).isoformat()
        elif idx < 6:
            estado = 'en_juego'
            fecha = base_date.isoformat()
        else:
            estado = 'programado'
            fecha = (base_date + timedelta(days=random.randint(1, 30))).isoformat()

        partido, error = crear_partido(
            id_liga,
            eq1['id'],
            eq2['id'],
            fecha,
            estado,
            headers
        )

        if partido:
            partidos_creados.append(partido)
            resumen['partidos'] += 1
            print(f"  ✓ {eq1['nombre']} vs {eq2['nombre']} - {estado}")
        else:
            print(f"  ~ Partido {eq1['nombre']} vs {eq2['nombre']}: {error or 'ya existe'}")

    # 4. Crear eventos para partidos finalizados
    print(f"\nCreando eventos para partidos finalizados...")
    partidos_finalizados = [p for p in partidos_creados if p.get('estado') == 'finalizado']

    for partido in partidos_finalizados:
        id_partido = partido['id']
        num_goles = random.randint(1, 5)

        # Obtener jugadores de ambos equipos
        id_local = partido['id_equipo_local']
        id_visitante = partido['id_equipo_visitante']
        jugadores_local = jugadores_por_equipo.get(id_local, [])
        jugadores_visitante = jugadores_por_equipo.get(id_visitante, [])
        todos_jugadores = jugadores_local + jugadores_visitante

        if not todos_jugadores:
            print(f"  ~ Sin jugadores para eventos en partido {id_partido}")
            continue

        print(f"  Partido {id_partido}: {num_goles} goles...")
        for _ in range(num_goles):
            jugador = random.choice(todos_jugadores)
            minuto = random.randint(1, 90)
            evento, error = crear_evento(
                id_partido,
                jugador['id'],
                'gol',
                minuto,
                headers
            )
            if evento:
                resumen['eventos'] += 1
            # else: print(f"    ✗ Error evento: {error}")

    return resumen

def main():
    print("="*60)
    print("GENERADOR DE DATOS DE PRUEBA - GOALAPP")
    print("="*60)

    # Login
    print("\n[1] Autenticando...")
    try:
        token = login()
        print(f"  ✓ Token obtenido exitosamente")
        headers = {'Authorization': f'Bearer {token}'}
    except Exception as e:
        print(f"  ✗ Error autenticando: {e}")
        return

    # Obtener ligas
    print("\n[2] Obteniendo ligas...")
    try:
        ligas = obtener_ligas(headers)
        print(f"  ✓ {len(ligas)} ligas encontradas:")
        for liga in ligas:
            print(f"    - {liga['nombre']} (ID: {liga['id']})")
    except Exception as e:
        print(f"  ✗ Error obteniendo ligas: {e}")
        return

    if not ligas:
        print("  ! No hay ligas disponibles")
        return

    # Generar datos por liga
    print("\n[3] Generando datos de prueba...")
    todos_resumenes = []

    for liga in ligas:
        resumen = generar_datos_liga(liga, headers)
        todos_resumenes.append(resumen)

    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)

    total = {
        'ligas': len(todos_resumenes),
        'equipos': 0,
        'usuarios': 0,
        'jugadores': 0,
        'partidos': 0,
        'eventos': 0
    }

    for resumen in todos_resumenes:
        print(f"\nLiga: {resumen['liga']} (ID: {resumen['id_liga']})")
        print(f"  Equipos: {resumen['equipos']}")
        print(f"  Usuarios: {resumen['usuarios']}")
        print(f"  Jugadores: {resumen['jugadores']}")
        print(f"  Partidos: {resumen['partidos']}")
        print(f"  Eventos: {resumen['eventos']}")

        total['equipos'] += resumen['equipos']
        total['usuarios'] += resumen['usuarios']
        total['jugadores'] += resumen['jugadores']
        total['partidos'] += resumen['partidos']
        total['eventos'] += resumen['eventos']

    print(f"\n{'='*60}")
    print(f"TOTAL GENERAL")
    print(f"{'='*60}")
    print(f"  Ligas procesadas: {total['ligas']}")
    print(f"  Equipos creados: {total['equipos']}")
    print(f"  Usuarios creados: {total['usuarios']}")
    print(f"  Jugadores creados: {total['jugadores']}")
    print(f"  Partidos creados: {total['partidos']}")
    print(f"  Eventos creados: {total['eventos']}")

if __name__ == '__main__':
    main()
