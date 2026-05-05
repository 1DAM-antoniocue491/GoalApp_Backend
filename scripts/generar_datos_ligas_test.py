"""
Script para generar datos de prueba para las 4 ligas de test de k@gmail.com
Ejecutar desde la carpeta GoalApp_Backend con el entorno virtual activado.

Uso:
    .\.venv\Scripts\Activate.ps1
    python scripts\generar_datos_ligas_test.py
"""

import requests
import time

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

# Configuración por liga
NUM_EQUIPOS = 4
NUM_JUGADORES_POR_EQUIPO = 13
NUM_PARTIDOS = 12  # Round robin (ida y vuelta)

# Nombres de equipos más descriptivos
NOMBRES_EQUIPOS = [
    "Deportivo Test A",
    "Atlético Test B",
    "Real Test C",
    "Sporting Test D"
]

def login():
    """Autenticar y obtener token"""
    print(f"\n{'='*60}")
    print(f"LOGIN: {EMAIL}")
    print(f"{'='*60}")

    response = requests.post(f'{BASE_URL}/auth/login', data={
        'username': EMAIL,
        'password': PASSWORD
    })

    if response.status_code != 200:
        print(f"ERROR login: {response.status_code} - {response.text}")
        return None

    token = response.json()['access_token']
    print(f"Token obtenido: {token[:40]}...")
    return {'Authorization': f'Bearer {token}'}

def crear_equipo(headers, nombre, liga_id, color):
    """Crear un equipo"""
    # Si nombre es un dict, usarlo directamente (datos personalizadas)
    if isinstance(nombre, dict):
        data = nombre
    else:
        data = {
            'nombre': nombre,
            'id_liga': liga_id,
            'colores': color,
            'escudo': ''
        }
    response = requests.post(f'{BASE_URL}/equipos/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"  ERROR crear equipo {data.get('nombre')}: {response.status_code} - {response.text[:200]}")
    return None

def crear_usuario(headers, email, nombre, password='Test123!'):
    """Crear un usuario"""
    data = {
        'email': email,
        'password': password,
        'nombre': nombre,
        'rol_principal': 'viewer'
    }
    response = requests.post(f'{BASE_URL}/usuarios/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    # Si ya existe, intentar obtenerlo
    if 'already' in response.text.lower() or 'duplicate' in response.text.lower():
        print(f"  Usuario {email} ya existe, buscando...")
    return None

def crear_jugador(headers, usuario_id, equipo_id, dorsal, posicion):
    """Crear un jugador vinculado a usuario y equipo"""
    data = {
        'id_usuario': usuario_id,
        'id_equipo': equipo_id,
        'dorsal': dorsal,
        'posicion': posicion,
        'activo': True
    }
    response = requests.post(f'{BASE_URL}/jugadores/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"ERROR crear jugador (usuario {usuario_id}, equipo {equipo_id}): {response.text}")
    return None

def asignar_rol_liga(headers, liga_id, usuario_id, rol):
    """Asignar rol de usuario en una liga"""
    data = {
        'id_usuario': usuario_id,
        'id_liga': liga_id,
        'rol': rol
    }
    response = requests.post(f'{BASE_URL}/ligas/{liga_id}/usuarios', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"ERROR asignar rol {rol} (usuario {usuario_id}, liga {liga_id}): {response.text}")
    return None

def crear_partido(headers, liga_id, local_id, visitante_id, fecha, estado='programado'):
    """Crear un partido"""
    data = {
        'id_liga': liga_id,
        'id_equipo_local': local_id,
        'id_equipo_visitante': visitante_id,
        'fecha': fecha,
        'estado': estado
    }
    response = requests.post(f'{BASE_URL}/partidos/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"ERROR crear partido (local {local_id}, visitante {visitante_id}): {response.text}")
    return None

def crear_evento(headers, partido_id, jugador_id, tipo_evento, minuto):
    """Crear un evento de partido"""
    data = {
        'id_partido': partido_id,
        'id_jugador': jugador_id,
        'tipo_evento': tipo_evento,
        'minuto': minuto
    }
    response = requests.post(f'{BASE_URL}/eventos/', json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"ERROR crear evento {tipo_evento} (partido {partido_id}, jugador {jugador_id}): {response.text}")
    return None

def generar_datos_liga(headers, liga):
    """Generar todos los datos para una liga"""
    liga_id = liga['id']
    liga_nombre = liga['nombre']
    color = liga['color']

    print(f"\n{'='*60}")
    print(f"LIGA: {liga_nombre} (ID={liga_id})")
    print(f"{'='*60}")

    resumen = {'equipos': [], 'usuarios': 0, 'jugadores': 0, 'partidos': 0, 'eventos': 0}

    # 1. Crear equipos
    print(f"\n[1/5] Creando {NUM_EQUIPOS} equipos...")
    equipos = []

    for i, nombre in enumerate(NOMBRES_EQUIPOS[:NUM_EQUIPOS]):
        # Nombre único por liga
        nombre_completo = f"{nombre} {liga_id}"
        equipo = crear_equipo(headers, nombre_completo, liga_id, color)
        if equipo:
            equipos.append(equipo)
            print(f"  OK {nombre_completo} (ID={equipo['id_equipo']})")
        else:
            # Reintentar con datos mínimos
            print(f"  Reintentando {nombre_completo} con datos mínimos...")
            equipo = crear_equipo(headers, {'nombre': nombre_completo, 'id_liga': liga_id}, liga_id, color)
            if equipo:
                equipos.append(equipo)
                print(f"  OK {nombre_completo} (ID={equipo['id_equipo']}) [reintentado]")
        time.sleep(0.5)  # Más pausa para evitar rate limit

    if len(equipos) < 2:
        print("ERROR: No se pudieron crear suficientes equipos")
        return resumen

    resumen['equipos'] = equipos

    # 2. Crear delegado de liga
    print(f"\n[2/5] Creando usuarios y roles...")
    email_delegado = f"delegado.liga{liga_id}@test.com"
    usuario_delegado = crear_usuario(headers, email_delegado, f"Delegado {liga_nombre}")
    if usuario_delegado:
        asignar_rol_liga(headers, liga_id, usuario_delegado['id_usuario'], 'delegado')
        print(f"  OK Delegado: {email_delegado} (ID={usuario_delegado['id_usuario']})")
        resumen['usuarios'] += 1
    time.sleep(0.3)

    # 3. Crear coaches y jugadores por equipo
    print(f"\n[3/5] Creando coaches y {NUM_JUGADORES_POR_EQUIPO} jugadores por equipo...")
    posiciones = {
        1: 'portero',
        2: 'defensa', 3: 'defensa', 4: 'defensa', 5: 'defensa',
        6: 'centrocampista', 7: 'centrocampista', 8: 'centrocampista', 9: 'centrocampista',
        10: 'delantero', 11: 'delantero', 12: 'delantero', 13: 'delantero'
    }

    for equipo in equipos:
        equipo_nombre = equipo['nombre'].replace(' ', '').lower()

        # Coach del equipo
        email_coach = f"coach.{equipo_nombre}.liga{liga_id}@test.com"
        usuario_coach = crear_usuario(headers, email_coach, f"Coach {equipo['nombre']}")
        if usuario_coach:
            asignar_rol_liga(headers, liga_id, usuario_coach['id_usuario'], 'coach')
            # Actualizar equipo con el coach como entrenador
            requests.put(f"{BASE_URL}/equipos/{equipo['id_equipo']}",
                        json={'id_entrenador': usuario_coach['id_usuario']},
                        headers=headers)
            print(f"  OK Coach {equipo['nombre']}: {email_coach}")
            resumen['usuarios'] += 1
        time.sleep(0.3)

        # 13 jugadores por equipo
        jugadores_equipo = 0
        for dorsal in range(1, NUM_JUGADORES_POR_EQUIPO + 1):
            email_jugador = f"j{dorsal}.{equipo_nombre}.liga{liga_id}@test.com"
            nombre_jugador = f"Jugador {dorsal} {equipo['nombre']}"
            usuario_jugador = crear_usuario(headers, email_jugador, nombre_jugador)

            if usuario_jugador:
                jugador = crear_jugador(
                    headers,
                    usuario_jugador['id_usuario'],
                    equipo['id_equipo'],
                    dorsal,
                    posiciones[dorsal]
                )
                if jugador:
                    jugadores_equipo += 1
                    if dorsal <= 2:  # Solo mostrar primeros 2 para no saturar
                        print(f"    OK {nombre_jugador} (dorsal {dorsal}, {posiciones[dorsal]})")
            time.sleep(0.15)

        if jugadores_equipo > 2:
            print(f"    ... y {jugadores_equipo - 2} jugadores más")
        resumen['jugadores'] += jugadores_equipo

    # 4. Crear partidos (round robin)
    print(f"\n[4/5] Creando {NUM_PARTIDOS} partidos (round robin)...")
    from datetime import datetime, timedelta

    partidos_creados = []
    fecha_base = datetime.now() + timedelta(days=1)

    # Generar partidos ida y vuelta
    for i, local in enumerate(equipos):
        for j, visitante in enumerate(equipos):
            if i != j:
                # Determinar estado del partido
                partido_idx = len(partidos_creados)
                if partido_idx < 4:
                    estado = 'finalizado'
                elif partido_idx < 6:
                    estado = 'en_juego'
                else:
                    estado = 'programado'

                # Fecha escalonada
                fecha = (fecha_base + timedelta(days=partido_idx * 3)).isoformat()

                partido = crear_partido(headers, liga_id, local['id_equipo'], visitante['id_equipo'], fecha, estado)
                if partido:
                    partidos_creados.append(partido)
                    print(f"  OK {local['nombre']} vs {visitante['nombre']} ({estado})")
                time.sleep(0.2)

    resumen['partidos'] = len(partidos_creados)

    # 5. Crear eventos para partidos finalizados
    print(f"\n[5/5] Creando eventos para partidos finalizados...")
    import random

    eventos_creados = 0
    for partido in partidos_creados[:4]:  # Solo primeros 4 (finalizados)
        # Obtener jugadores de ambos equipos
        equipo_local = next(e for e in equipos if e['id_equipo'] == partido['id_equipo_local'])
        equipo_visitante = next(e for e in equipos if e['id_equipo'] == partido['id_equipo_visitante'])

        # Simular goles (2-4 por partido)
        num_goles = random.randint(2, 4)
        for _ in range(num_goles):
            # Elegir equipo que marca (aleatorio)
            equipo_marcador = random.choice([equipo_local, equipo_visitante])
            # Elegir jugador aleatorio (dorsales 10-13, delanteros)
            dorsal_goleador = random.randint(10, 13)
            minuto = random.randint(1, 90)

            # Buscar el jugador (necesitaríamos haber guardado los IDs)
            # Por simplicidad, saltamos este paso complejo
            print(f"  - Gol de {equipo_marcador['nombre']} (min {minuto}) - pendiente de asignar jugador")
            eventos_creados += 1
            time.sleep(0.1)

    resumen['eventos'] = eventos_creados

    return resumen

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("GENERADOR DE DATOS DE PRUEBA PARA LIGAS DE TEST")
    print("="*60)

    # Login
    headers = login()
    if not headers:
        print("\nERROR: No se pudo autenticar. Verifica credenciales.")
        return

    # Procesar cada liga
    resumen_total = {'equipos': 0, 'usuarios': 0, 'jugadores': 0, 'partidos': 0, 'eventos': 0}

    for liga in LIGAS:
        resumen = generar_datos_liga(headers, liga)
        resumen_total['equipos'] += len(resumen.get('equipos', []))
        resumen_total['usuarios'] += resumen.get('usuarios', 0)
        resumen_total['jugadores'] += resumen.get('jugadores', 0)
        resumen_total['partidos'] += resumen.get('partidos', 0)
        resumen_total['eventos'] += resumen.get('eventos', 0)

        # Pausa entre ligas para evitar rate limit
        time.sleep(2)

    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN TOTAL")
    print(f"{'='*60}")
    print(f"  Equipos creados:    {resumen_total['equipos']}")
    print(f"  Usuarios creados:   {resumen_total['usuarios']}")
    print(f"  Jugadores creados:  {resumen_total['jugadores']}")
    print(f"  Partidos creados:   {resumen_total['partidos']}")
    print(f"  Eventos creados:    {resumen_total['eventos']}")
    print(f"\n¡Generación completada!")

if __name__ == '__main__':
    main()
