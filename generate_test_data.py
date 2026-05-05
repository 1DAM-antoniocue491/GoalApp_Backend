import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = 'http://localhost:8000/api/v1'

def login():
    """Autenticar con k@gmail.com"""
    response = requests.post(f'{BASE_URL}/auth/login', data={
        'username': 'k@gmail.com',
        'password': 'k12345'
    })
    response.raise_for_status()
    return response.json()['access_token']

def get_leagues(token):
    """Obtener ligas del usuario"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/usuarios/me/ligas', headers=headers)
    response.raise_for_status()
    return response.json()

def create_equipo(token, nombre, id_liga, colores="#000000", escudo=""):
    """Crear un equipo"""
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "nombre": nombre,
        "id_liga": id_liga,
        "colores": colores,
        "escudo": escudo
    }
    response = requests.post(f'{BASE_URL}/equipos/', headers=headers, json=data)
    if response.status_code == 400:
        # Equipo ya existe, buscarlo
        response = requests.get(f'{BASE_URL}/ligas/{id_liga}/equipos', headers=headers)
        equipos = response.json()
        for eq in equipos:
            if eq['nombre'] == nombre:
                return eq['id']
        return None
    response.raise_for_status()
    return response.json()['id_equipo']

def create_usuario(token, email, password, nombre, rol_principal="jugador"):
    """Crear un usuario"""
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "email": email,
        "password": password,
        "nombre": nombre,
        "rol_principal": rol_principal
    }
    response = requests.post(f'{BASE_URL}/usuarios/', headers=headers, json=data)
    if response.status_code == 400:
        # Usuario ya existe
        return None
    response.raise_for_status()
    return response.json()['id']

def get_usuario_by_email(token, email):
    """Buscar usuario por email"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/usuarios/?search={email}', headers=headers)
    response.raise_for_status()
    usuarios = response.json()
    if usuarios:
        return usuarios[0]['id']
    return None

def create_jugador(token, id_usuario, id_equipo, dorsal, posicion, activo=True):
    """Crear un jugador"""
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "id_usuario": id_usuario,
        "id_equipo": id_equipo,
        "dorsal": dorsal,
        "posicion": posicion,
        "activo": activo
    }
    response = requests.post(f'{BASE_URL}/jugadores/', headers=headers, json=data)
    if response.status_code == 400:
        # Jugador ya existe
        return None
    response.raise_for_status()
    return response.json()['id']

def create_partido(token, id_liga, id_local, id_visitante, fecha, estado="programado"):
    """Crear un partido"""
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "id_liga": id_liga,
        "id_equipo_local": id_local,
        "id_equipo_visitante": id_visitante,
        "fecha": fecha,
        "estado": estado
    }
    response = requests.post(f'{BASE_URL}/partidos/', headers=headers, json=data)
    if response.status_code == 400:
        return None
    response.raise_for_status()
    return response.json()['id']

def create_evento(token, id_partido, id_jugador, tipo_evento, minuto):
    """Crear un evento de partido"""
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "id_partido": id_partido,
        "id_jugador": id_jugador,
        "tipo_evento": tipo_evento,
        "minuto": minuto
    }
    response = requests.post(f'{BASE_URL}/eventos/', headers=headers, json=data)
    if response.status_code == 400:
        return None
    response.raise_for_status()
    return response.json()['id']

def get_jugadores_by_equipo(token, id_equipo):
    """Obtener jugadores de un equipo"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/equipos/{id_equipo}/jugadores', headers=headers)
    response.raise_for_status()
    return response.json()

def get_partidos_by_liga(token, id_liga):
    """Obtener partidos de una liga"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/ligas/{id_liga}/partidos', headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    print("=" * 60)
    print("GENERANDO DATOS DE PRUEBA PARA LIGAS DE TEST")
    print("=" * 60)

    # Paso 1: Login
    print("\n[1] Autenticando...")
    token = login()
    print("    Token obtenido exitosamente")

    # Paso 2: Obtener ligas
    print("\n[2] Obteniendo ligas...")
    ligas = get_leagues(token)
    print(f"    Ligas encontradas: {len(ligas)}")

    resumen = []

    for liga in ligas:
        id_liga = liga['id_liga']
        nombre_liga = liga['nombre']
        print(f"\n{'='*60}")
        print(f"PROCESANDO LIGA: {nombre_liga} (ID: {id_liga})")
        print(f"{'='*60}")

        liga_resumen = {
            'liga': nombre_liga,
            'id_liga': id_liga,
            'equipos': 0,
            'usuarios': 0,
            'jugadores': 0,
            'partidos': 0,
            'eventos': 0
        }

        # Crear 4 equipos
        equipos_nombres = ["Equipo A", "Equipo B", "Equipo C", "Equipo D"]
        equipos_ids = []

        print(f"\n[3] Creando equipos...")
        for i, nombre_eq in enumerate(equipos_nombres):
            equipo_id = create_equipo(token, nombre_eq, id_liga)
            if equipo_id:
                equipos_ids.append(equipo_id)
                print(f"    Equipo '{nombre_eq}' creado (ID: {equipo_id})")
                liga_resumen['equipos'] += 1

        if not equipos_ids:
            # Obtener equipos existentes
            response = requests.get(f'{BASE_URL}/ligas/{id_liga}/equipos',
                                  headers={'Authorization': f'Bearer {token}'})
            equipos_existentes = response.json()
            equipos_ids = [eq['id'] for eq in equipos_existentes[:4]]
            print(f"    Usando {len(equipos_ids)} equipos existentes")

        # Crear usuarios y jugadores por equipo
        print(f"\n[4] Creando usuarios y jugadores...")
        suffix = f".liga{id_liga}"

        for idx_equipo, equipo_id in enumerate(equipos_ids):
            nombre_equipo = equipos_nombres[idx_equipo] if idx_equipo < len(equipos_nombres) else f"Equipo {idx_equipo+1}"
            equipo_suffix = f".equipo{chr(97+idx_equipo)}{suffix}"  # .equipoa.liga1

            # Crear coach
            coach_email = f"coach{equipo_suffix}@test.com"
            coach_id = create_usuario(token, coach_email, "password123",
                                     f"Coach {nombre_equipo}", "entrenador")
            if coach_id:
                print(f"    Coach creado: {coach_email}")
                liga_resumen['usuarios'] += 1

            # Crear delegado (solo uno por equipo)
            delegado_email = f"delegado{equipo_suffix}@test.com"
            delegado_id = create_usuario(token, delegado_email, "password123",
                                        f"Delegado {nombre_equipo}", "delegado")
            if delegado_id:
                print(f"    Delegado creado: {delegado_email}")
                liga_resumen['usuarios'] += 1

            # Crear 13 jugadores
            posiciones = ['portero'] + ['defensa']*4 + ['centrocampista']*4 + ['delantero']*4
            jugadores_ids = []

            for j in range(13):
                jugador_email = f"jugador{j+1}{equipo_suffix}@test.com"
                jugador_nombre = f"Jugador {j+1} {nombre_equipo}"

                usuario_id = create_usuario(token, jugador_email, "password123",
                                           jugador_nombre, "jugador")

                if usuario_id:
                    liga_resumen['usuarios'] += 1
                else:
                    # Buscar usuario existente
                    usuario_id = get_usuario_by_email(token, jugador_email)

                if usuario_id:
                    dorsal = j + 1
                    posicion = posiciones[j]
                    jugador_id = create_jugador(token, usuario_id, equipo_id, dorsal, posicion)
                    if jugador_id:
                        jugadores_ids.append(jugador_id)
                        liga_resumen['jugadores'] += 1
                    else:
                        # Buscar jugadores existentes del equipo
                        pass

            print(f"    Equipo {nombre_equipo}: {len(jugadores_ids)} jugadores creados")

        # Obtener jugadores reales de cada equipo (por si algunos ya existían)
        todos_jugadores = []
        for equipo_id in equipos_ids:
            jugadores = get_jugadores_by_equipo(token, equipo_id)
            todos_jugadores.extend(jugadores)

        print(f"\n[5] Creando partidos...")
        # Crear 15 partidos (round-robin entre 4 equipos = 12 partidos + 3 extra)
        partidos_creados = 0
        fecha_base = datetime.now()

        # Round-robin: cada equipo juega contra los demás 2 veces (local y visitante)
        partidos_programados = []
        for i, local_id in enumerate(equipos_ids):
            for j, visitante_id in enumerate(equipos_ids):
                if i != j:
                    partidos_programados.append((local_id, visitante_id))

        # Crear partidos
        for idx, (local_id, visitante_id) in enumerate(partidos_programados[:12]):
            fecha = fecha_base + timedelta(days=idx*3)
            partido_id = create_partido(token, id_liga, local_id, visitante_id,
                                       fecha.strftime("%Y-%m-%dT%H:%M:%S"))
            if partido_id:
                partidos_creados += 1
                liga_resumen['partidos'] += 1

        print(f"    {partidos_creados} partidos programados creados")

        # Actualizar algunos partidos a "finalizado" y "en_juego"
        print(f"\n[6] Actualizando estados de partidos...")
        partidos = get_partidos_by_liga(token, id_liga)

        partidos_finalizados = []
        partidos_en_juego = []

        for partido in partidos[:6]:
            if partido['estado'] == 'programado':
                # Actualizar a finalizado o en_juego
                headers = {'Authorization': f'Bearer {token}'}
                if len(partidos_finalizados) < 4:
                    data = {"estado": "finalizado"}
                    response = requests.put(f'{BASE_URL}/partidos/{partido["id"]}',
                                          headers=headers, json=data)
                    if response.status_code == 200:
                        partidos_finalizados.append(partido)
                        print(f"    Partido {partido['id']} -> finalizado")
                elif len(partidos_en_juego) < 2:
                    data = {"estado": "en_juego"}
                    response = requests.put(f'{BASE_URL}/partidos/{partido["id"]}',
                                          headers=headers, json=data)
                    if response.status_code == 200:
                        partidos_en_juego.append(partido)
                        print(f"    Partido {partido['id']} -> en_juego")

        # Crear eventos para partidos finalizados
        print(f"\n[7] Creando eventos para partidos finalizados...")
        eventos_creados = 0

        for partido in partidos_finalizados:
            # Crear 1-5 goles por partido
            num_goles = random.randint(1, 5)
            for _ in range(num_goles):
                if todos_jugadores:
                    jugador = random.choice(todos_jugadores)
                    minuto = random.randint(1, 90)
                    evento_id = create_evento(token, partido['id'], jugador['id'],
                                            "gol", minuto)
                    if evento_id:
                        eventos_creados += 1
                        liga_resumen['eventos'] += 1

            print(f"    Partido {partido['id']}: {num_goles} eventos creados")

        resumen.append(liga_resumen)

    # Imprimir resumen final
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"\nLigas procesadas: {len(resumen)}")

    for r in resumen:
        print(f"\n{r['liga']} (ID: {r['id_liga']}):")
        print(f"  - Equipos: {r['equipos']}")
        print(f"  - Usuarios: {r['usuarios']}")
        print(f"  - Jugadores: {r['jugadores']}")
        print(f"  - Partidos: {r['partidos']}")
        print(f"  - Eventos: {r['eventos']}")

    print(f"\n{'='*60}")
    print("GENERACION COMPLETADA")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
