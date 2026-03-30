#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para generar datos de ejemplo en GoalApp."""
import requests
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_TOKEN = None

def login(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception(f"Error en login: {response.text}")

def get_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def crear_usuario(nombre, email, password):
    response = requests.post(f"{BASE_URL}/usuarios/", json={"nombre": nombre, "email": email, "password": password})
    if response.status_code == 200:
        return response.json()
    return None

def asignar_rol(token, usuario_id, rol_id):
    response = requests.post(f"{BASE_URL}/roles/asignar/{usuario_id}/{rol_id}", headers=get_headers(token))
    return response.status_code == 200

def crear_liga(token, nombre, temporada):
    response = requests.post(f"{BASE_URL}/ligas/", headers=get_headers(token), json={"nombre": nombre, "temporada": temporada})
    if response.status_code == 200:
        return response.json()
    return None

def crear_equipo(token, nombre, id_liga, id_entrenador, id_delegado, colores=None):
    data = {"nombre": nombre, "id_liga": id_liga, "id_entrenador": id_entrenador, "id_delegado": id_delegado}
    if colores:
        data["colores"] = colores
    response = requests.post(f"{BASE_URL}/equipos/", headers=get_headers(token), json=data)
    if response.status_code == 200:
        return response.json()
    return None

def crear_jugador(token, id_usuario, id_equipo, posicion, dorsal):
    response = requests.post(f"{BASE_URL}/jugadores/", headers=get_headers(token), json={"id_usuario": id_usuario, "id_equipo": id_equipo, "posicion": posicion, "dorsal": dorsal})
    if response.status_code == 200:
        return response.json()
    return None

def crear_partido(token, id_liga, id_local, id_visitante, fecha, estado="programado"):
    response = requests.post(f"{BASE_URL}/partidos/", headers=get_headers(token), json={"id_liga": id_liga, "id_equipo_local": id_local, "id_equipo_visitante": id_visitante, "fecha": fecha.isoformat(), "estado": estado})
    if response.status_code == 200:
        return response.json()
    return None

def crear_evento(token, id_partido, id_jugador, tipo_evento, minuto):
    response = requests.post(f"{BASE_URL}/eventos/", headers=get_headers(token), json={"id_partido": id_partido, "id_jugador": id_jugador, "tipo_evento": tipo_evento, "minuto": minuto})
    if response.status_code == 200:
        return response.json()
    return None

def actualizar_partido(token, id_partido, goles_local, goles_visitante, estado="finalizado"):
    response = requests.put(f"{BASE_URL}/partidos/{id_partido}", headers=get_headers(token), json={"goles_local": goles_local, "goles_visitante": goles_visitante, "estado": estado})
    if response.status_code == 200:
        return response.json()
    return None

def main():
    global ADMIN_TOKEN

    print("=" * 60)
    print("GENERANDO DATOS DE EJEMPLO PARA GOALAPP")
    print("=" * 60)

    print("\n[1] INICIANDO SESION COMO ADMIN...")
    ADMIN_TOKEN = login("antonio@gmail.com", "123456789")
    print("    OK - Login exitoso")

    print("\n[2] CREANDO USUARIOS...")
    usuarios = []

    entrenadores = [
        {"nombre": "Carlos Martinez", "email": "carlos.martinez@email.com"},
        {"nombre": "Luis Fernandez", "email": "luis.fernandez@email.com"},
        {"nombre": "Miguel Sanchez", "email": "miguel.sanchez@email.com"},
        {"nombre": "Pedro Ruiz", "email": "pedro.ruiz@email.com"},
        {"nombre": "Raul Garcia", "email": "raul.garcia@email.com"},
        {"nombre": "Fernando Torres", "email": "fernando.torres@email.com"},
        {"nombre": "Diego Lopez", "email": "diego.lopez@email.com"},
        {"nombre": "Javier Moreno", "email": "javier.moreno@email.com"},
    ]

    delegados = [
        {"nombre": "Ana Gomez", "email": "ana.gomez@email.com"},
        {"nombre": "Maria Rodriguez", "email": "maria.rodriguez@email.com"},
        {"nombre": "Laura Perez", "email": "laura.perez@email.com"},
        {"nombre": "Sara Jimenez", "email": "sara.jimenez@email.com"},
        {"nombre": "Carmen Diaz", "email": "carmen.diaz@email.com"},
        {"nombre": "Lucia Navarro", "email": "lucia.navarro@email.com"},
        {"nombre": "Elena Molina", "email": "elena.molina@email.com"},
        {"nombre": "Rosa Serrano", "email": "rosa.serrano@email.com"},
    ]

    equipos_nombres = ["Atletico Villa", "Real Puerto", "Deportivo Sierra", "Union Costa", "Club Norte", "Atletico Sur", "Deportivo Este", "Union Oeste"]
    posiciones = ["Portero", "Defensa", "Defensa", "Centrocampista", "Centrocampista", "Centrocampista", "Delantero", "Delantero", "Delantero", "Delantero"]

    jugadores_data = []
    for i, equipo in enumerate(equipos_nombres):
        for j in range(10):
            jugadores_data.append({"nombre": f"Jugador {j+1} {equipo}", "email": f"jugador{j+1}.{equipo.lower().replace(' ', '.')}@email.com", "equipo_idx": i, "posicion": posiciones[j], "dorsal": j + 1})

    print("    Creando entrenadores...")
    for ent in entrenadores:
        user = crear_usuario(ent["nombre"], ent["email"], "123456789")
        if user:
            asignar_rol(ADMIN_TOKEN, user["id_usuario"], 2)
            usuarios.append(user)
            print(f"    OK - {ent['nombre']} (coach)")

    print("    Creando delegados...")
    for delg in delegados:
        user = crear_usuario(delg["nombre"], delg["email"], "123456789")
        if user:
            asignar_rol(ADMIN_TOKEN, user["id_usuario"], 5)
            usuarios.append(user)
            print(f"    OK - {delg['nombre']} (delegate)")

    print("    Creando jugadores...")
    for jug in jugadores_data:
        user = crear_usuario(jug["nombre"], jug["email"], "123456789")
        if user:
            asignar_rol(ADMIN_TOKEN, user["id_usuario"], 3)
            usuarios.append(user)

    print(f"    Total jugadores creados: {len(jugadores_data)}")

    print("\n[3] CREANDO LIGA...")
    liga = crear_liga(ADMIN_TOKEN, "Liga Amateur Sevilla 2025/2026", "2025/2026")
    if liga:
        print(f"    OK - Liga: {liga['nombre']} (ID: {liga['id_liga']})")
    else:
        print("    ERROR - No se pudo crear la liga")
        return

    print("\n[4] CREANDO EQUIPOS...")
    equipos = []
    colores_equipos = ["Rojo y Blanco", "Azul y Blanco", "Verde y Negro", "Amarillo y Azul", "Blanco y Negro", "Rojo y Negro", "Azul y Rojo", "Verde y Blanco"]

    for i, nombre in enumerate(equipos_nombres):
        equipo = crear_equipo(ADMIN_TOKEN, nombre, liga["id_liga"], usuarios[i]["id_usuario"], usuarios[i + 8]["id_usuario"], colores_equipos[i])
        if equipo:
            equipos.append(equipo)
            print(f"    OK - {nombre}")

    print("\n[5] CREANDO JUGADORES...")
    jugadores_creados = []
    jugadores_start_idx = 16

    for i, jug_data in enumerate(jugadores_data):
        usuario = usuarios[jugadores_start_idx + i]
        equipo = equipos[jug_data["equipo_idx"]]
        jugador = crear_jugador(ADMIN_TOKEN, usuario["id_usuario"], equipo["id_equipo"], jug_data["posicion"], jug_data["dorsal"])
        if jugador:
            jugadores_creados.append(jugador)

    print(f"    Total jugadores creados: {len(jugadores_creados)}")

    print("\n[6] CREANDO PARTIDOS...")
    partidos = []
    fecha_base = datetime(2025, 9, 6, 17, 0)
    partido_num = 0

    for i in range(len(equipos)):
        for j in range(i + 1, len(equipos)):
            if (i + j) % 2 == 0:
                local, visitante = equipos[i], equipos[j]
            else:
                local, visitante = equipos[j], equipos[i]

            dias_add = (partido_num // 2) * 7
            hora = 17 if partido_num % 2 == 0 else 19
            fecha_partido = fecha_base + timedelta(days=dias_add)
            fecha_partido = fecha_partido.replace(hour=hora)

            partido = crear_partido(ADMIN_TOKEN, liga["id_liga"], local["id_equipo"], visitante["id_equipo"], fecha_partido)
            if partido:
                partidos.append(partido)
                print(f"    OK - {local['nombre']} vs {visitante['nombre']}")

            partido_num += 1

    print(f"    Total partidos creados: {len(partidos)}")

    print("\n[7] SIMULANDO RESULTADOS...")
    resultados = [(3, 1), (2, 2), (0, 1), (4, 0)]

    for idx, (goles_local, goles_visitante) in enumerate(resultados):
        if idx >= len(partidos):
            break

        partido = partidos[idx]
        actualizar_partido(ADMIN_TOKEN, partido["id_partido"], goles_local, goles_visitante, "finalizado")
        print(f"    OK - Partido {idx+1}: {goles_local} - {goles_visitante}")

        jugadores_local = [j for j in jugadores_creados if j["id_equipo"] == partido["id_equipo_local"]]
        jugadores_visitante = [j for j in jugadores_creados if j["id_equipo"] == partido["id_equipo_visitante"]]

        for g in range(goles_local + goles_visitante):
            if g < goles_local:
                jugador = random.choice(jugadores_local)
            else:
                jugador = random.choice(jugadores_visitante)
            crear_evento(ADMIN_TOKEN, partido["id_partido"], jugador["id_jugador"], "gol", random.randint(1, 90))

        for _ in range(random.randint(1, 3)):
            jugador = random.choice(jugadores_local + jugadores_visitante)
            tipo = random.choice(["tarjeta_amarilla", "tarjeta_amarilla", "tarjeta_roja"])
            crear_evento(ADMIN_TOKEN, partido["id_partido"], jugador["id_jugador"], tipo, random.randint(1, 90))

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  Liga:         1")
    print(f"  Usuarios:     {len(usuarios)}")
    print(f"    - Entrenadores: 8")
    print(f"    - Delegados:    8")
    print(f"    - Jugadores:    80")
    print(f"  Equipos:       {len(equipos)}")
    print(f"  Jugadores:     {len(jugadores_creados)}")
    print(f"  Partidos:      {len(partidos)}")
    print(f"    - Finalizados: 4")
    print(f"    - Programados: {len(partidos) - 4}")
    print("=" * 60)
    print("\nOK - DATOS DE EJEMPLO GENERADOS CORRECTAMENTE!")

if __name__ == "__main__":
    main()