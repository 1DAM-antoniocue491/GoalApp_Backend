# Script robusto para generar datos de prueba para las 4 ligas de test.
# Verifica datos existentes antes de crear para evitar duplicados.
#
# Uso:
#     cd C:\\Users\\Antonio\\Desktop\\GoalApp\\GoalApp_Backend
#     python scripts/generar_datos_completos.py

import requests
import time
from datetime import datetime, timedelta
import random

# Configuración
BASE_URL = 'https://goalapp-backend-j2cx.onrender.com/api/v1'
EMAIL = 'k@gmail.com'
PASSWORD = 'k12345'

# Ligas de test a poblar
LIGAS = [
    {'id': 54, 'nombre': 'Liga Delegado Test', 'color': 'azul'},
    {'id': 55, 'nombre': 'Liga Jugador Test', 'color': 'rojo'},
    {'id': 60, 'nombre': 'Liga Entrenador Test', 'color': 'verde'},
    {'id': 62, 'nombre': 'Liga Viewer Test', 'color': 'amarillo'},
]

# Nombres de equipos
NOMBRES_EQUIPOS = [
    "Deportivo Test",
    "Atlético Test",
    "Real Test",
    "Sporting Test"
]

def login():
    print(f"\n{'='*60}")
    print(f"LOGIN: {EMAIL}")
    print(f"{'='*60}")
    response = requests.post(f'{BASE_URL}/auth/login', data={'username': EMAIL, 'password': PASSWORD})
    if response.status_code != 200:
        print(f"ERROR login: {response.status_code}")
        return None
    token = response.json()['access_token']
    print(f"Token: {token[:40]}...")
    return {'Authorization': f'Bearer {token}'}

def obtener_equipos_liga(headers, liga_id):
    """Obtener equipos existentes de una liga"""
    response = requests.get(f'{BASE_URL}/equipos/', params={'liga_id': liga_id}, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def obtener_usuarios_liga(headers, liga_id):
    """Obtener usuarios con rol en una liga"""
    response = requests.get(f'{BASE_URL}/usuarios/ligas/{liga_id}/usuarios', headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def crear_equipo(headers, nombre, liga_id, color):
    data = {'nombre': nombre, 'id_liga': liga_id, 'colores': color, 'escudo': ''}
    response = requests.post(f'{BASE_URL}/equipos/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    # Si falla, intentar con datos mínimos
    data_min = {'nombre': nombre, 'id_liga': liga_id}
    response = requests.post(f'{BASE_URL}/equipos/', json=data_min, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"  ERROR crear {nombre}: {response.status_code}")
    return None

def crear_usuario_si_no_existe(headers, email, nombre, rol_principal='viewer'):
    """Crear usuario si no existe, o buscarlo si ya existe"""
    # Primero intentar crear
    data = {'email': email, 'password': 'Test123!', 'nombre': nombre, 'rol_principal': rol_principal}
    response = requests.post(f'{BASE_URL}/usuarios/', json=data, headers=headers)

    if response.status_code == 200:
        return response.json(), True  # Nuevo usuario

    # Si ya existe (400 o 409), buscarlo en la lista de usuarios
    if response.status_code in [400, 409]:
        # Obtener lista de usuarios para buscar el existente
        response = requests.get(f'{BASE_URL}/usuarios/', headers=headers)
        if response.status_code == 200:
            usuarios = response.json()
            for usuario in usuarios:
                if usuario.get('email') == email:
                    return usuario, False  # Usuario existente
    return None, False

def crear_jugador(headers, usuario_id, equipo_id, dorsal, posicion):
    data = {'id_usuario': usuario_id, 'id_equipo': equipo_id, 'dorsal': dorsal, 'posicion': posicion, 'activo': True}
    response = requests.post(f'{BASE_URL}/jugadores/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"  ERROR crear jugador: {response.text[:100]}")
    return None

def crear_partido(headers, liga_id, local_id, visitante_id, fecha, estado):
    data = {'id_liga': liga_id, 'id_equipo_local': local_id, 'id_equipo_visitante': visitante_id, 'fecha': fecha, 'estado': estado}
    response = requests.post(f'{BASE_URL}/partidos/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"  ERROR crear partido: {response.text[:100]}")
    return None

def generar_datos_liga(headers, liga):
    liga_id = liga['id']
    liga_nombre = liga['nombre']
    color = liga['color']

    print(f"\n{'='*60}")
    print(f"LIGA: {liga_nombre} (ID={liga_id})")
    print(f"{'='*60}")

    resumen = {'equipos': 0, 'usuarios': 0, 'jugadores': 0, 'partidos': 0}

    # Verificar datos existentes
    print(f"\n[1/6] Verificando datos existentes...")
    equipos_existentes = obtener_equipos_liga(headers, liga_id)
    usuarios_existentes = obtener_usuarios_liga(headers, liga_id)

    print(f"  Equipos existentes: {len(equipos_existentes)}")
    print(f"  Usuarios con rol: {len(usuarios_existentes)}")

    # Si ya hay 4+ equipos, saltar a siguientes pasos
    if len(equipos_existentes) >= 4:
        print("  [OK] La liga ya tiene equipos, usando existentes...")
        equipos = equipos_existentes[:4]
    else:
        # Crear equipos faltantes
        print(f"\n[2/6] Creando equipos...")
        equipos = equipos_existentes.copy()

        for i, nombre_base in enumerate(NOMBRES_EQUIPOS):
            if len(equipos) >= 4:
                break
            nombre = f"{nombre_base} {liga_id}"
            print(f"  Creando {nombre}...")
            equipo = crear_equipo(headers, nombre, liga_id, color)
            if equipo:
                equipos.append(equipo)
                print(f"    OK {nombre} (ID={equipo['id_equipo']})")
            time.sleep(0.5)

    if len(equipos) < 4:
        print(f"ERROR: No se pudieron crear 4 equipos ({len(equipos)} creados)")
        return resumen

    resumen['equipos'] = len(equipos)

    # Crear delegado si no existe
    print(f"\n[3/6] Verificando/creando delegado...")
    email_delegado = f"delegado.liga{liga_id}@test.com"
    usuario_delegado, nuevo = crear_usuario_si_no_existe(headers, email_delegado, f"Delegado {liga_nombre}", 'delegado')
    if usuario_delegado:
        print(f"  {'OK (nuevo)' if nuevo else 'OK (existente)'}: {email_delegado}")
        resumen['usuarios'] += 1 if nuevo else 0
    time.sleep(0.3)

    # Crear coaches y jugadores por equipo
    print(f"\n[4/6] Creando coaches y 13 jugadores por equipo...")
    posiciones = {
        1: 'portero', 2: 'defensa', 3: 'defensa', 4: 'defensa', 5: 'defensa',
        6: 'centrocampista', 7: 'centrocampista', 8: 'centrocampista', 9: 'centrocampista',
        10: 'delantero', 11: 'delantero', 12: 'delantero', 13: 'delantero'
    }

    for equipo in equipos:
        equipo_nombre = equipo['nombre'].replace(' ', '').lower()

        # Coach
        email_coach = f"coach.{equipo_nombre}.liga{liga_id}@test.com"
        usuario_coach, nuevo = crear_usuario_si_no_existe(headers, email_coach, f"Coach {equipo['nombre']}", 'coach')
        if usuario_coach:
            print(f"  Coach {equipo['nombre']}: {email_coach} {'(nuevo)' if nuevo else '(existente)'}")
            resumen['usuarios'] += 1 if nuevo else 0
            # Actualizar equipo con entrenador
            requests.put(f"{BASE_URL}/equipos/{equipo['id_equipo']}",
                        json={'id_entrenador': usuario_coach['id_usuario']},
                        headers=headers)
        time.sleep(0.3)

        # 13 jugadores
        jugadores_creados = 0
        for dorsal in range(1, 14):
            email_jugador = f"j{dorsal}.{equipo_nombre}.liga{liga_id}@test.com"
            nombre_jugador = f"Jugador {dorsal} {equipo['nombre']}"
            usuario_jugador, nuevo = crear_usuario_si_no_existe(headers, email_jugador, nombre_jugador, 'viewer')

            if usuario_jugador:
                jugador = crear_jugador(headers, usuario_jugador['id_usuario'], equipo['id_equipo'], dorsal, posiciones[dorsal])
                if jugador:
                    jugadores_creados += 1
            time.sleep(0.1)

        print(f"  Equipo {equipo['nombre']}: {jugadores_creados} jugadores")
        resumen['jugadores'] += jugadores_creados

    # Crear partidos
    print(f"\n[5/6] Creando partidos...")
    partidos_creados = []
    fecha_base = datetime.now() + timedelta(days=1)

    # Verificar partidos existentes
    response = requests.get(f'{BASE_URL}/partidos/', params={'liga_id': liga_id}, headers=headers)
    partidos_existentes = response.json() if response.status_code == 200 else []
    print(f"  Partidos existentes: {len(partidos_existentes)}")

    if len(partidos_existentes) >= 12:
        print("  [OK] La liga ya tiene 12+ partidos, usando existentes...")
        partidos_creados = partidos_existentes[:12]
    else:
        # Crear partidos round-robin
        for i, local in enumerate(equipos):
            for j, visitante in enumerate(equipos):
                if i != j and len(partidos_creados) < 12:
                    idx = len(partidos_creados)
                    estado = 'finalizado' if idx < 4 else ('en_juego' if idx < 6 else 'programado')
                    fecha = (fecha_base + timedelta(days=idx * 3)).isoformat()

                    partido = crear_partido(headers, liga_id, local['id_equipo'], visitante['id_equipo'], fecha, estado)
                    if partido:
                        partidos_creados.append(partido)
                        print(f"  OK {local['nombre']} vs {visitante['nombre']} ({estado})")
                    time.sleep(0.2)

    resumen['partidos'] = len(partidos_creados)

    # Eventos para partidos finalizados (opcional, complejo)
    print(f"\n[6/6] Eventos - Pendiente de implementación completa")

    return resumen

def main():
    print("\n" + "="*60)
    print("GENERADOR DE DATOS DE PRUEBA - LIGAS DE TEST")
    print("="*60)

    headers = login()
    if not headers:
        print("\nERROR: No se pudo autenticar")
        return

    resumen_total = {'equipos': 0, 'usuarios': 0, 'jugadores': 0, 'partidos': 0}

    for liga in LIGAS:
        resumen = generar_datos_liga(headers, liga)
        resumen_total['equipos'] += resumen.get('equipos', 0)
        resumen_total['usuarios'] += resumen.get('usuarios', 0)
        resumen_total['jugadores'] += resumen.get('jugadores', 0)
        resumen_total['partidos'] += resumen.get('partidos', 0)
        time.sleep(2)  # Rate limit entre ligas

    print(f"\n{'='*60}")
    print("RESUMEN TOTAL")
    print(f"{'='*60}")
    print(f"  Equipos:     {resumen_total['equipos']}")
    print(f"  Usuarios:    {resumen_total['usuarios']}")
    print(f"  Jugadores:   {resumen_total['jugadores']}")
    print(f"  Partidos:    {resumen_total['partidos']}")
    print(f"\n¡Generación completada!")

if __name__ == '__main__':
    main()
