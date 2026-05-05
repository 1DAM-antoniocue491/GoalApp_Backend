#!/usr/bin/env python3
"""
Script de integración con la API de GoalApp para:
1. Loguearse
2. Crear una liga
3. Crear 4 equipos
4. Generar código de invitación para jugador
"""

import requests
from typing import Optional
import json

BASE_URL = "https://goalapp-backend-j2cx.onrender.com/api/v1"

# Credenciales
EMAIL = "k@gmail.com"
PASSWORD = "k12345"

# Datos para la liga y equipos
LIGA_NOMBRE = "Liga Jugador Test"
EQUIPOS_NOMBRES = [
    "FC Test 1",
    "FC Test 2",
    "FC Test 3",
    "FC Test 4"
]

class GoalAppAPI:
    """Cliente para la API de GoalApp"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()

    def login(self, email: str, password: str) -> dict:
        """
        Realiza login y obtiene tokens de acceso.

        Args:
            email: Email del usuario
            password: Contraseña

        Returns:
            dict con access_token, refresh_token, token_type, expires_in
        """
        url = f"{self.base_url}/auth/login"

        # El endpoint espera form-data con username (no email) y password
        data = {
            "username": email,  # OAuth2PasswordRequestForm usa 'username'
            "password": password
        }

        print(f"[*] Intentando login con email: {email}")
        response = self.session.post(url, data=data)

        if response.status_code != 200:
            raise Exception(f"Login fallido: {response.status_code} - {response.text}")

        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]

        # Configurar header de autorización para futuras peticiones
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })

        print(f"[+] Login exitoso!")
        print(f"    Access Token: {self.access_token[:50]}...")
        print(f"    Refresh Token: {self.refresh_token[:50]}...")

        return tokens

    def crear_liga(self, nombre: str, pais: str = "España", temporada: str = "2025/2026") -> dict:
        """
        Crea una nueva liga.

        Args:
            nombre: Nombre de la liga
            pais: País de la liga
            temporada: Temporada

        Returns:
            dict con información de la liga creada
        """
        url = f"{self.base_url}/ligas/"

        data = {
            "nombre": nombre,
            "pais": pais,
            "temporada": temporada
        }

        print(f"\n[*] Creando liga: {nombre}")
        response = self.session.post(url, json=data)

        if response.status_code != 200:
            raise Exception(f"Error creando liga: {response.status_code} - {response.text}")

        liga = response.json()
        print(f"[+] Liga creada exitosamente!")
        print(f"    ID Liga: {liga['id_liga']}")
        print(f"    Nombre: {liga['nombre']}")
        print(f"    País: {liga['pais']}")
        print(f"    Temporada: {liga['temporada']}")

        return liga

    def crear_equipo(self, nombre: str, id_liga: int, ciudad: str = "Madrid") -> dict:
        """
        Crea un nuevo equipo en una liga.

        Args:
            nombre: Nombre del equipo
            id_liga: ID de la liga
            ciudad: Ciudad del equipo

        Returns:
            dict con información del equipo creado
        """
        url = f"{self.base_url}/equipos/"

        data = {
            "nombre": nombre,
            "id_liga": id_liga,
            "ciudad": ciudad,
            "colores": "Azul y Blanco"
        }

        print(f"\n[*] Creando equipo: {nombre} (Liga {id_liga})")
        response = self.session.post(url, json=data)

        if response.status_code != 200:
            raise Exception(f"Error creando equipo: {response.status_code} - {response.text}")

        equipo = response.json()
        print(f"[+] Equipo creado exitosamente!")
        print(f"    ID Equipo: {equipo['id_equipo']}")
        print(f"    Nombre: {equipo['nombre']}")
        print(f"    Liga: {equipo['id_liga']}")

        return equipo

    def generar_codigo_invitacion(self, liga_id: int, id_rol: int, id_equipo: int,
                                   dorsal: int = 10, posicion: str = "Delantero",
                                   nombre: str = "Jugador Test") -> dict:
        """
        Genera un código de invitación para un rol específico.

        Args:
            liga_id: ID de la liga
            id_rol: ID del rol (4 = Jugador)
            id_equipo: ID del equipo
            dorsal: Número dorsal (para jugador)
            posicion: Posición del jugador
            nombre: Nombre descriptivo para la invitación

        Returns:
            dict con código de invitación
        """
        url = f"{self.base_url}/invitaciones/ligas/{liga_id}/generar-codigo"

        data = {
            "id_rol": id_rol,
            "id_equipo": id_equipo,
            "dorsal": dorsal,
            "posicion": posicion,
            "nombre": nombre,
            "tipo_jugador": "titular"
        }

        print(f"\n[*] Generando código de invitación (Rol {id_rol}, Equipo {id_equipo})")
        response = self.session.post(url, json=data)

        if response.status_code != 201:
            raise Exception(f"Error generando código: {response.status_code} - {response.text}")

        invitacion = response.json()
        print(f"[+] Código generado exitosamente!")
        print(f"    Código: {invitacion['codigo']}")
        print(f"    Rol: {invitacion['rol']}")
        print(f"    Liga: {invitacion['liga']}")
        print(f"    Expiración: {invitacion['expiracion']}")

        return invitacion


def main():
    """Función principal que ejecuta todo el flujo"""

    print("=" * 60)
    print("INTEGRACIÓN CON API DE GOALAPP")
    print("=" * 60)

    # Inicializar cliente
    api = GoalAppAPI(BASE_URL)

    # 1. Login
    print("\n" + "=" * 60)
    print("PASO 1: LOGIN")
    print("=" * 60)
    tokens = api.login(EMAIL, PASSWORD)

    # 2. Crear liga
    print("\n" + "=" * 60)
    print("PASO 2: CREAR LIGA")
    print("=" * 60)
    liga = api.crear_liga(LIGA_NOMBRE)
    liga_id = liga["id_liga"]

    # 3. Crear 4 equipos
    print("\n" + "=" * 60)
    print("PASO 3: CREAR 4 EQUIPOS")
    print("=" * 60)
    equipos_creados = []
    for nombre in EQUIPOS_NOMBRES:
        equipo = api.crear_equipo(nombre, liga_id)
        equipos_creados.append(equipo)

    # 4. Generar código de invitación para JUGADOR (id_rol=4)
    print("\n" + "=" * 60)
    print("PASO 4: GENERAR CÓDIGO DE INVITACIÓN (JUGADOR)")
    print("=" * 60)
    # Usamos el primer equipo para la invitación
    primer_equipo_id = equipos_creados[0]["id_equipo"]
    codigo_invitacion = api.generar_codigo_invitacion(
        liga_id=liga_id,
        id_rol=4,  # Rol de jugador
        id_equipo=primer_equipo_id,
        dorsal=10,
        posicion="Delantero",
        nombre="Jugador Test"
    )

    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"""
    TOKEN DE ACCESO:
    {tokens['access_token']}

    ID DE LA LIGA CREADA:
    {liga_id}

    CÓDIGO DE INVITACIÓN (JUGADOR):
    {codigo_invitacion['codigo']}

    EQUIPOS CREADOS:
    {json.dumps([{'nombre': e['nombre'], 'id': e['id_equipo']} for e in equipos_creados], indent=2)}
    """)

    # Guardar resultados en un archivo JSON
    resultados = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "liga_id": liga_id,
        "liga_nombre": liga["nombre"],
        "codigo_invitacion": codigo_invitacion["codigo"],
        "equipos": [{"nombre": e["nombre"], "id_equipo": e["id_equipo"]} for e in equipos_creados]
    }

    output_file = "C:\\Users\\Antonio\\Desktop\\GoalApp\\GoalApp_Backend\\resultados_test.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n[+] Resultados guardados en: {output_file}")
    print("\n" + "=" * 60)
    print("INTEGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()
