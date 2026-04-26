# Documentacion del Backend - Liga Amateur App

## Indice

1. [Introduccion](#introduccion)
2. [Conceptos Fundamentales](#conceptos-fundamentales)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Tecnologias Utilizadas](#tecnologias-utilizadas)
5. [Configuracion del Entorno](#configuracion-del-entorno)
6. [Base de Datos](#base-de-datos)
7. [API REST - Endpoints](#api-rest---endpoints)
8. [Sistema de Autenticacion](#sistema-de-autenticacion)
9. [Validacion de Datos](#validacion-de-datos)
10. [Arquitectura del Codigo](#arquitectura-del-codigo)
11. [Guia de Desarrollo](#guia-de-desarrollo)

---

## Introduccion

Este backend es una **API REST** que gestiona una aplicacion de ligas de futbol amateur. Permite administrar:

- **Usuarios y Roles**: Sistema de autenticacion con diferentes niveles de acceso
- **Ligas y Equipos**: Organizacion de competiciones
- **Jugadores**: Registro de participantes
- **Partidos y Eventos**: Seguimiento de partidos en tiempo real
- **Notificaciones**: Sistema de avisos

---

## Conceptos Fundamentales

### Que es una API REST?

Una **API REST** (Representational State Transfer) es una forma de comunicacion entre sistemas a traves de HTTP. Funciona como un "camarero" que toma tu pedido (request) y te trae lo que pediste (response).

```
Cliente (App Movil/Web) <---> API REST <---> Base de Datos
```

### Metodos HTTP

| Metodo | Uso | Ejemplo |
|--------|-----|---------|
| GET | Obtener datos | Ver lista de equipos |
| POST | Crear nuevos datos | Registrar un usuario |
| PUT | Actualizar datos existentes | Cambiar nombre de equipo |
| DELETE | Eliminar datos | Borrar un jugador |

### Codigos de Estado HTTP

| Codigo | Significado | Cuando se usa |
|--------|-------------|---------------|
| 200 | OK | Operacion exitosa |
| 201 | Created | Recurso creado correctamente |
| 400 | Bad Request | Datos invalidos |
| 401 | Unauthorized | No autenticado |
| 403 | Forbidden | Sin permisos |
| 404 | Not Found | Recurso no encontrado |
| 500 | Server Error | Error interno |

---

## Estructura del Proyecto

```
backend/
├── .env.example            # Plantilla de variables de entorno
├── requirements.txt        # Librerias necesarias
└── app/
    ├── main.py             # Punto de entrada de la aplicacion
    ├── config.py           # Configuracion centralizada
    ├── database/
    │   └── connection.py   # Conexion a la base de datos
    ├── models/             # Modelos de la base de datos (tablas)
    │   ├── usuario.py
    │   ├── rol.py
    │   ├── equipo.py
    │   └── ... (13 archivos)
    ├── schemas/            # Esquemas de validacion
    │   ├── usuario.py
    │   ├── rol.py
    │   └── ... (13 archivos)
    └── api/
        ├── dependencies.py # Dependencias compartidas (auth, db)
        ├── routers/        # Endpoints de la API
        │   ├── auth.py
        │   ├── usuarios.py
        │   └── ... (10 archivos)
        └── services/       # Logica de negocio
            ├── usuario_service.py
            └── ... (9 archivos)
```

### Que hace cada carpeta?

| Carpeta | Funcion |
|---------|---------|
| `models/` | Define como son las tablas en la base de datos |
| `schemas/` | Define que datos entran y salen de la API |
| `routers/` | Define los endpoints (URLs) de la API |
| `services/` | Contiene la logica de negocio |

---

## Tecnologias Utilizadas

### Python 3.13
Lenguaje de programacion principal. Es facil de leer y escribir.

### FastAPI
Framework web moderno para crear APIs. Es como un "constructor" que facilita crear endpoints.

**Caracteristicas:**
- Documentacion automatica (Swagger UI)
- Validacion de datos integrada
- Rendimiento alto

### SQLAlchemy (ORM)
Permite interactuar con la base de datos usando codigo Python en lugar de SQL.

```python
# En lugar de escribir:
# SELECT * FROM usuarios WHERE id = 1

# Escribimos:
db.query(Usuario).filter(Usuario.id_usuario == 1).first()
```

### Pydantic
Valida que los datos tengan el formato correcto antes de procesarlos.

```python
# Ejemplo: El email debe ser valido
class UsuarioBase(BaseModel):
    nombre: str                    # Obligatorio
    email: EmailStr                # Debe ser email valido
```

### PostgreSQL
Base de datos relacional donde se almacenan todos los datos.

### JWT (JSON Web Tokens)
Sistema de autenticacion. Es como una "credencial digital" que demuestra quien eres.

---

## Configuracion del Entorno

### Archivo .env

El archivo `.env` contiene las variables de configuracion sensibles:

```env
# Base de Datos
DATABASE_URL=postgresql+psycopg2://usuario:password@localhost:5432/futbol_app
DATABASE_ECHO=True

# Seguridad JWT
SECRET_KEY=<clave secreta>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Aplicacion
APP_NAME=Liga Amateur App
API_VERSION=v1
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0

# CORS (Origenes permitidos)
CORS_ORIGINS=http://localhost:3000,http://localhost:19006

# Logging
LOG_LEVEL=INFO
```

### Variables Explicadas

| Variable                      | Descripcion                                      |
| ----------------------------- | ------------------------------------------------ |
| `DATABASE_URL`                | Direccion de conexion a PostgreSQL                    |
| `SECRET_KEY`                  | Clave secreta para firmar tokens (no compartir!) |
| `ALGORITHM`                   | Algoritmo de encriptacion (HS256)                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tiempo de vida del token (60 min)                |
| `CORS_ORIGINS`                | URLs permitidas para hacer peticiones            |

### Instalacion de Dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar el Servidor

```bash
# Desde la carpeta backend
python -m uvicorn app.main:app --reload
```

El servidor estara disponible en: `http://127.0.0.1:8000`

---

## Base de Datos

### Diagrama Entidad-Relacion

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  usuarios   │───┬───│ usuario_rol │───┬───│    roles    │
└─────────────┘   │   └─────────────┘   │   └─────────────┘
      │           │                     │
      │           └─────────────────────┘
      │
      ├──────────────────────┐
      │                      │
      ▼                      ▼
┌─────────────┐       ┌─────────────┐
│  jugadores  │       │   equipos   │
└─────────────┘       └─────────────┘
      │                      │
      │                      │
      ▼                      ▼
┌───────────────┐     ┌─────────────┐
│eventos_partido│     │   ligas     │
└───────────────┘     └─────────────┘
      │                      │
      └──────────┬───────────┘
                 ▼
          ┌─────────────┐
          │  partidos   │
          └─────────────┘
                 │
                 ▼
          ┌─────────────┐
          │  partidos   │
          └─────────────┘
```

### Tablas de la Base de Datos

#### usuarios
Almacena los usuarios del sistema.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_usuario | INT (PK) | Identificador unico |
| nombre | VARCHAR(100) | Nombre completo |
| email | VARCHAR(100) | Email (unico, para login) |
| contrasena_hash | VARCHAR(255) | Contrasena encriptada |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

#### roles
Define los roles disponibles en el sistema.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_rol | INT (PK) | Identificador unico |
| nombre | VARCHAR(50) | Nombre del rol (admin, coach, player, etc.) |
| descripcion | VARCHAR(255) | Descripcion del rol |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

**Roles predefinidos:**
- `admin` - Administrador (acceso total)
- `coach` - Entrenador (gestiona su equipo)
- `delegate` - Delegado (gestiona su equipo)
- `player` - Jugador (ver sus datos)
- `viewer` - Espectador (solo lectura)

#### usuario_rol
Tabla intermedia para relacionar usuarios con roles (relacion N:N).

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_usuario_rol | INT (PK) | Identificador unico |
| id_usuario | INT (FK) | Referencia a usuarios |
| id_rol | INT (FK) | Referencia a roles |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

#### ligas
Competiciones de futbol.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_liga | INT (PK) | Identificador unico |
| nombre | VARCHAR(100) | Nombre de la liga |
| temporada | VARCHAR(20) | Temporada (ej: "2024/2025") |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

#### equipos
Equipos de futbol.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_equipo | INT (PK) | Identificador unico |
| nombre | VARCHAR(100) | Nombre del equipo |
| escudo | VARCHAR(255) | URL del escudo (opcional) |
| colores | VARCHAR(50) | Colores del equipo |
| id_liga | INT (FK) | Liga a la que pertenece |
| id_entrenador | INT (FK) | Usuario entrenador |
| id_delegado | INT (FK) | Usuario delegado |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

#### jugadores
Jugadores de cada equipo.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_jugador | INT (PK) | Identificador unico |
| id_usuario | INT (FK) | Usuario asociado (unico) |
| id_equipo | INT (FK) | Equipo al que pertenece |
| posicion | VARCHAR(50) | Posicion (Portero, Defensa, etc.) |
| dorsal | INT | Numero de camiseta (1-99) |
| activo | BOOLEAN | Esta activo? (default: True) |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

**Posiciones comunes:**
- Portero
- Defensa
- Lateral
- Medio
- Delantero

#### partidos
Partidos programados.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_partido | INT (PK) | Identificador unico |
| id_liga | INT (FK) | Liga del partido |
| id_equipo_local | INT (FK) | Equipo local |
| id_equipo_visitante | INT (FK) | Equipo visitante |
| fecha | DATETIME | Fecha y hora |
| estado | VARCHAR(50) | Estado del partido |
| goles_local | INT | Goles del local (opcional) |
| goles_visitante | INT | Goles del visitante (opcional) |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

**Estados de partido:**
- `programado` - Pendiente de jugar
- `en_juego` - En curso
- `finalizado` - Terminado
- `cancelado` - Suspendido

#### eventos_partido
Eventos ocurridos durante un partido.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_evento | INT (PK) | Identificador unico |
| id_partido | INT (FK) | Partido del evento |
| id_jugador | INT (FK) | Jugador involucrado |
| tipo_evento | VARCHAR(50) | Tipo de evento |
| minuto | INT | Minuto del evento (1-120) |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

**Tipos de evento:**
- `gol` - Gol marcado
- `tarjeta_amarilla` - Amonestacion
- `tarjeta_roja` - Expulsion
- `cambio` - Sustitucion
- `mvp` - Mejor jugador

#### notificaciones
Mensajes para usuarios.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_notificacion | INT (PK) | Identificador unico |
| id_usuario | INT (FK) | Usuario destinatario |
| mensaje | TEXT | Contenido del mensaje |
| leida | BOOLEAN | Ha sido leida? |
| created_at | DATETIME | Fecha de creacion |
| updated_at | DATETIME | Fecha de actualizacion |

---

## API REST - Endpoints

### URL Base

```
http://localhost:8000/api/v1
```

### Documentacion Interactiva

FastAPI genera documentacion automatica:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Autenticacion

#### POST /auth/login
Iniciar sesion y obtener token.

**Request:**
```json
{
  "username": "usuario@email.com",
  "password": "tu_contrasena"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET /auth/me
Obtener usuario actual (requiere token).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id_usuario": 1,
  "nombre": "Juan Garcia",
  "email": "juan@email.com"
}
```

---

### Usuarios

#### POST /usuarios/
Crear nuevo usuario.

**Request:**
```json
{
  "nombre": "Juan Garcia",
  "email": "juan@email.com",
  "contraseña": "secreta123"
}
```

**Response:** (201 Created)
```json
{
  "id_usuario": 1,
  "nombre": "Juan Garcia",
  "email": "juan@email.com",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

#### GET /usuarios/
Listar usuarios (requiere rol admin).

**Response:**
```json
[
  {
    "id_usuario": 1,
    "nombre": "Juan Garcia",
    "email": "juan@email.com",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

#### GET /usuarios/{id}
Obtener usuario por ID.

#### PUT /usuarios/{id}
Actualizar usuario.

**Request:**
```json
{
  "nombre": "Juan Garcia Lopez",
  "email": "juan.nuevo@email.com"
}
```

#### DELETE /usuarios/{id}
Eliminar usuario (requiere rol admin).

---

### Roles

#### POST /roles/
Crear rol (requiere rol admin).

**Request:**
```json
{
  "nombre": "arbitro",
  "descripcion": "Arbitro de partidos"
}
```

#### GET /roles/
Listar todos los roles.

#### POST /roles/asignar/{usuario_id}/{rol_id}
Asignar rol a usuario (requiere rol admin).

---

### Ligas

#### POST /ligas/
Crear liga (requiere rol admin).

**Request:**
```json
{
  "nombre": "Liga Municipal",
  "temporada": "2024/2025"
}
```

#### GET /ligas/
Listar ligas.

#### GET /ligas/{id}
Obtener liga por ID.

#### PUT /ligas/{id}
Actualizar liga.

#### DELETE /ligas/{id}
Eliminar liga.

---

### Equipos

#### POST /equipos/
Crear equipo (requiere rol admin).

**Request:**
```json
{
  "nombre": "Atletico Villa",
  "escudo": "https://ejemplo.com/escudo.png",
  "colores": "Rojo y Blanco",
  "id_liga": 1,
  "id_entrenador": 2,
  "id_delegado": 3
}
```

#### GET /equipos/
Listar equipos.

#### GET /equipos/{id}
Obtener equipo por ID.

#### PUT /equipos/{id}
Actualizar equipo.

#### DELETE /equipos/{id}
Eliminar equipo.

---

### Jugadores

#### POST /jugadores/
Crear jugador (requiere rol admin).

**Request:**
```json
{
  "id_usuario": 5,
  "id_equipo": 1,
  "posicion": "Delantero",
  "dorsal": 9,
  "activo": true
}
```

#### GET /jugadores/
Listar jugadores.

#### GET /jugadores/{id}
Obtener jugador por ID.

#### PUT /jugadores/{id}
Actualizar jugador.

#### DELETE /jugadores/{id}
Eliminar jugador.

---

### Partidos

#### POST /partidos/
Crear partido (requiere rol admin).

**Request:**
```json
{
  "id_liga": 1,
  "id_equipo_local": 1,
  "id_equipo_visitante": 2,
  "fecha": "2024-03-15T18:00:00",
  "estado": "programado"
}
```

#### GET /partidos/
Listar partidos.

#### GET /partidos/{id}
Obtener partido por ID.

#### PUT /partidos/{id}
Actualizar partido (goles, estado, etc.).

**Request:**
```json
{
  "estado": "finalizado",
  "goles_local": 2,
  "goles_visitante": 1
}
```

#### DELETE /partidos/{id}
Eliminar partido.

---

### Eventos de Partido

#### POST /eventos/
Registrar evento (requiere rol admin).

**Request:**
```json
{
  "id_partido": 1,
  "id_jugador": 5,
  "tipo_evento": "gol",
  "minuto": 35
}
```

#### GET /eventos/partido/{partido_id}
Listar eventos de un partido.

**Response:**
```json
[
  {
    "id_evento": 1,
    "id_partido": 1,
    "id_jugador": 5,
    "tipo_evento": "gol",
    "minuto": 35,
    "created_at": "2024-03-15T18:35:00"
  }
]
```

---

### Notificaciones

#### GET /notificaciones/
Listar notificaciones del usuario autenticado.

#### PUT /notificaciones/{id}
Marcar como leida.

**Request:**
```json
{
  "leida": true
}
```

---

## Sistema de Autenticacion

### Como Funciona JWT

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cliente    │────>│   API REST   │────>│ Base Datos   │
│  (App Móvil) │     │  (FastAPI)   │     │ (PostgreSQL) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       │  1. Login          │                     │
       │  (email + pass)    │                     │
       │ ──────────────────>│                     │
       │                    │  2. Verificar       │
       │                    │ ───────────────────>│
       │                    │                     │
       │                    │  3. Usuario valido  │
       │                    │ <───────────────────│
       │                    │                     │
       │  4. Token JWT      │                     │
       │ <──────────────────│                     │
       │                    │                     │
       │  5. Peticion       │                     │
       │  + Token           │                     │
       │ ──────────────────>│                     │
       │                    │  6. Validar Token   │
       │                    │  (sin consultar BD) │
       │                    │                     │
       │  7. Datos          │                     │
       │ <──────────────────│                     │
```

### Que es un Token JWT?

Un JWT (JSON Web Token) es una cadena de texto con tres partes:

```
xxxxx.yyyyy.zzzzz
 │       │     │
 │       │     └── Firma (verifica autenticidad)
 │       └──────── Payload (datos del usuario)
 └──────────────── Header (tipo de token)
```

**Ejemplo decodificado:**

Header:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

Payload:
```json
{
  "sub": "1",           // ID del usuario
  "exp": 1704234567     // Fecha de expiracion
}
```

### Como Usar el Token

En cada peticion protegida, incluir el token en el header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Proteccion de Endpoints

Los endpoints se protegen usando dependencias:

```python
# Endpoint publico
@app.get("/ligas/")
def listar_ligas():
    ...

# Endpoint autenticado
@app.get("/usuarios/me")
def mi_perfil(usuario = Depends(get_current_user)):
    ...

# Endpoint solo para admins
@app.delete("/usuarios/{id}")
def eliminar_usuario(
    usuario = Depends(require_role("admin"))
):
    ...
```

---

## Validacion de Datos

### Que es Pydantic?

Pydantic es una libreria que valida automaticamente que los datos tengan el formato correcto.

**Ejemplo de validacion:**

```python
from pydantic import BaseModel, EmailStr, Field

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., max_length=100)  # Obligatorio, max 100 chars
    email: EmailStr                            # Debe ser email valido
    contrasena: str = Field(..., min_length=6) # Minimo 6 caracteres
```

Si enviamos datos incorrectos:

```json
{
  "nombre": "Juan",
  "email": "no-es-email",
  "contrasena": "123"
}
```

La API responde con error:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "contrasena"],
      "msg": "ensure this value has at least 6 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Tipos de Validacion

| Tipo | Ejemplo | Que valida |
|------|---------|------------|
| `str` | `nombre: str` | Texto obligatorio |
| `str \| None` | `escudo: str \| None` | Texto opcional |
| `int` | `dorsal: int` | Numero entero |
| `bool` | `activo: bool` | True o False |
| `EmailStr` | `email: EmailStr` | Formato de email |
| `datetime` | `fecha: datetime` | Fecha y hora |
| `Field(..., ge=1)` | `dorsal: int = Field(..., ge=1, le=99)` | Entre 1 y 99 |

### Esquemas por Recurso

Cada recurso tiene 4 tipos de esquemas:

```python
# 1. Base - Campos comunes
class JugadorBase(BaseModel):
    id_usuario: int
    id_equipo: int
    posicion: str
    dorsal: int

# 2. Create - Para crear (hereda de Base)
class JugadorCreate(JugadorBase):
    pass  # Usa los mismos campos obligatorios

# 3. Update - Para actualizar (todos opcionales)
class JugadorUpdate(BaseModel):
    id_usuario: int | None = None
    id_equipo: int | None = None
    posicion: str | None = None
    dorsal: int | None = None

# 4. Response - Para responder (incluye ID y timestamps)
class JugadorResponse(BaseModel):
    id_jugador: int
    id_usuario: int
    id_equipo: int
    posicion: str
    dorsal: int
    activo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Permite leer desde modelos ORM
```

---

## Arquitectura del Codigo

### Patron de Capas

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACION                 │
│                     (Routers / Endpoints)               │
│   - Define las URLs                                     │
│   - Valida entrada con schemas                          │
│   - Formatea salida                                     │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE SERVICIOS                    │
│                     (Services / Logica)                 │
│   - Logica de negocio                                   │
│   - Operaciones CRUD                                    │
│   - Validaciones complejas                              │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                        │
│                   (Models / SQLAlchemy)                 │
│   - Definicion de tablas                                │
│   - Relaciones entre tablas                             │
│   - Mapeo objeto-relacional                             │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    BASE DE DATOS                        │
│                     (PostgreSQL)                         │
└─────────────────────────────────────────────────────────┘
```

### Ejemplo de Flujo

**Request:** `POST /jugadores/`

1. **Router** (`routers/jugadores.py`):
   ```python
   @router.post("/", response_model=JugadorResponse)
   def crear_jugador(
       jugador: JugadorCreate,
       db: Session = Depends(get_db),
       current_user: Usuario = Depends(require_role("admin"))
   ):
       return jugador_service.crear_jugador(db, jugador)
   ```

2. **Service** (`services/jugador_service.py`):
   ```python
   def crear_jugador(db: Session, jugador: JugadorCreate) -> Jugador:
       # Verificar que el usuario existe
       usuario = db.query(Usuario).filter(
           Usuario.id_usuario == jugador.id_usuario
       ).first()
       if not usuario:
           raise HTTPException(404, "Usuario no encontrado")

       # Crear el jugador
       db_jugador = Jugador(**jugador.model_dump())
       db.add(db_jugador)
       db.commit()
       db.refresh(db_jugador)
       return db_jugador
   ```

3. **Model** (`models/jugador.py`):
   ```python
   class Jugador(Base):
       __tablename__ = "jugadores"

       id_jugador = Column(Integer, primary_key=True)
       id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
       id_equipo = Column(Integer, ForeignKey("equipos.id_equipo"))
       posicion = Column(String(50))
       dorsal = Column(Integer)
       activo = Column(Boolean, default=True)
   ```

4. **Schema** (`schemas/jugador.py`):
   ```python
   class JugadorResponse(BaseModel):
       id_jugador: int
       id_usuario: int
       id_equipo: int
       posicion: str
       dorsal: int
       activo: bool
       created_at: datetime
       updated_at: datetime

       class Config:
           from_attributes = True
   ```

### Inyeccion de Dependencias

FastAPI usa un sistema de dependencias para compartir codigo:

```python
# Obtener sesion de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener usuario actual desde token
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Decodificar token y buscar usuario
    ...

# Usar en endpoint
@router.get("/me")
def mi_perfil(
    usuario = Depends(get_current_user)  # Se inyecta automaticamente
):
    return usuario
```

---

## Guia de Desarrollo

### Agregar un Nuevo Endpoint

1. **Crear el schema** en `app/schemas/`:

```python
# app/schemas/nuevo_recurso.py
from pydantic import BaseModel
from datetime import datetime

class NuevoRecursoBase(BaseModel):
    nombre: str
    descripcion: str | None = None

class NuevoRecursoCreate(NuevoRecursoBase):
    pass

class NuevoRecursoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None

class NuevoRecursoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

2. **Crear el modelo** en `app/models/`:

```python
# app/models/nuevo_recurso.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database.connection import Base

class NuevoRecurso(Base):
    __tablename__ = "nuevos_recursos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

3. **Crear el servicio** en `app/api/services/`:

```python
# app/api/services/nuevo_recurso_service.py
from sqlalchemy.orm import Session
from ..models.nuevo_recurso import NuevoRecurso
from ..schemas.nuevo_recurso import NuevoRecursoCreate, NuevoRecursoUpdate

def crear(db: Session, item: NuevoRecursoCreate) -> NuevoRecurso:
    db_item = NuevoRecurso(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def obtener_todos(db: Session) -> list[NuevoRecurso]:
    return db.query(NuevoRecurso).all()

def obtener_por_id(db: Session, id: int) -> NuevoRecurso | None:
    return db.query(NuevoRecurso).filter(NuevoRecurso.id == id).first()

def actualizar(db: Session, id: int, item: NuevoRecursoUpdate) -> NuevoRecurso:
    db_item = obtener_por_id(db, id)
    if not db_item:
        return None
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def eliminar(db: Session, id: int) -> bool:
    db_item = obtener_por_id(db, id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True
```

4. **Crear el router** en `app/api/routers/`:

```python
# app/api/routers/nuevo_recurso.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from ..services import nuevo_recurso_service
from ...schemas.nuevo_recurso import (
    NuevoRecursoCreate,
    NuevoRecursoUpdate,
    NuevoRecursoResponse
)

router = APIRouter(prefix="/nuevo-recurso", tags=["Nuevo Recurso"])

@router.post("/", response_model=NuevoRecursoResponse)
def crear(
    item: NuevoRecursoCreate,
    db: Session = Depends(get_db)
):
    return nuevo_recurso_service.crear(db, item)

@router.get("/", response_model=list[NuevoRecursoResponse])
def listar_todos(db: Session = Depends(get_db)):
    return nuevo_recurso_service.obtener_todos(db)

@router.get("/{id}", response_model=NuevoRecursoResponse)
def obtener(id: int, db: Session = Depends(get_db)):
    item = nuevo_recurso_service.obtener_por_id(db, id)
    if not item:
        raise HTTPException(404, "Recurso no encontrado")
    return item

@router.put("/{id}", response_model=NuevoRecursoResponse)
def actualizar(
    id: int,
    item: NuevoRecursoUpdate,
    db: Session = Depends(get_db)
):
    result = nuevo_recurso_service.actualizar(db, id, item)
    if not result:
        raise HTTPException(404, "Recurso no encontrado")
    return result

@router.delete("/{id}")
def eliminar(id: int, db: Session = Depends(get_db)):
    if not nuevo_recurso_service.eliminar(db, id):
        raise HTTPException(404, "Recurso no encontrado")
    return {"mensaje": "Eliminado correctamente"}
```

5. **Registrar el router** en `app/main.py`:

```python
from .api.routers import nuevo_recurso

app.include_router(
    nuevo_recurso.router,
    prefix="/api/v1",
    tags=["Nuevo Recurso"]
)
```

6. **Importar el modelo** en `app/database/connection.py` o crear las tablas:

```python
from ..models.nuevo_recurso import NuevoRecurso
```

### Probar un Endpoint

Usa la documentacion interactiva en `http://localhost:8000/docs`:

1. Abre el navegador en `/docs`
2. Click en el endpoint a probar
3. Click en "Try it out"
4. Completa los parametros/body
5. Click en "Execute"
6. Ve la respuesta

O usa `curl`:

```bash
# Crear usuario
curl -X POST "http://localhost:8000/api/v1/usuarios/" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Juan", "email": "juan@email.com", "contrasena": "secreta123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=juan@email.com&password=secreta123"

# Con token
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

---

## Resumen

Este backend proporciona una API REST completa para gestionar ligas de futbol amateur con:

- **13 tablas** en la base de datos
- **10 routers** con endpoints CRUD
- **Sistema de autenticacion JWT** con roles
- **Validacion automatica** de datos
- **Documentacion interactiva** generada automaticamente

La arquitectura sigue el patron de capas:
1. **Routers** (endpoints)
2. **Services** (logica)
3. **Models** (datos)
4. **Schemas** (validacion)

Para desarrollo, siempre:
1. Crear schema
2. Crear modelo
3. Crear servicio
4. Crear router
5. Registrar en main.py