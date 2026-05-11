# ⚙️ GoalApp Backend

El backend de GoalApp es una API REST de alto rendimiento construida con **FastAPI**, diseñada bajo una arquitectura de capas para garantizar la seguridad, la escalabilidad y la integridad de los datos deportivos.

## 🛠️ Stack Tecnológico

- **Lenguaje**: Python 3.13
- **Framework**: FastAPI (v1)
- la **Servidor ASGI**: Uvicorn
- **ORM**: SQLAlchemy
- **Validación de Datos**: Pydantic (v2)
- **Base de Datos**: PostgreSQL (vía Supabase)
- **Migraciones**: Alembic
- **Seguridad**: JWT (`python-jose`) y Hashing con `Bcrypt`
- **Infraestructura**: Render (Producción)
- **Almacenamiento**: Supabase Storage (para imágenes y archivos)

---

## 🏗️ Arquitectura del Proyecto

El sistema implementa un patrón de diseño desacoplado donde el flujo de datos es estrictamente descendente:
`Request` $\rightarrow$ `Router` $\rightarrow$ `Service` $\rightarrow$ `Model` $\rightarrow$ `Database`

### 1. Capa de Presentación (`app/api/routers/`)
Responsable de la definición de los endpoints y la validación de los esquemas de entrada/salida.
- **Módulos Implementados**: Autenticación, Usuarios, Roles, Ligas, Equipivos, Jugadores, Partidos, Eventos, Convocatorias, Alineaciones, Invitaciones, Notificaciones e Imágenes.
- **Acceso Público**: Endpoint `public.py` para vistas y datos accesibles sin autenticación.

### 2. Capa de Lógica de Negocio (`app/api/services/`)
Cerebro de la aplicación. Aquí reside toda la validación de reglas deportivas y la orquestación de datos.
- **Servicios Específicos**: Lógica dedicada por entidad (ej. `liga_service.py`, `partido_service.py`).
- **Servicios Transversales**: Integraciones externas como `email_service.py` y `supabase_storage_service.py`.

### 3. Capa de Datos (`app/models/`)
Definición de la estructura de la base de datos mediante clases de SQLAlchemy.
- **Modelado**: Implementación de relaciones complejas (1:N, N:N) y claves foráneas para garantizar la integridad referencial.
- **Auditoría**: Implementación de campos `created_at` y `updated_at` en todas las entidades principales.

---

## 🔒 Seguridad y Control de Acceso

### Sistema de Roles (RBAC)
GoalApp implementa un control de acceso basado en roles estrictos mediante la dependencia `require_role`:
- **Admin**: Control global del sistema, creación de ligas y gestión de usuarios.
- **Coach**: Gestión de su equipo, plantillas y alineaciones.
- **Delegate**: Registro de eventos y resultados de partidos en tiempo real.
- **Player**: Consulta de estadísticas, perfil propio y calendario.
- **Viewer**: Acceso restringido a información pública.

### Autenticación JWT
- **Flujo**: Login $\rightarrow$ Generación de Token HS256 $\rightarrow$ Envío en Header `Authorization: Bearer <token>`.
- **Gestión de Sesión**: Expiración configurable mediante `ACCESS_TOKEN_EXPIRE_MINUTES` y soporte para el flujo de refresco de tokens.

---

## 🚀 Instalación y Ejecución Local

### Requisitos
- Python 3.13+
- Instancia de PostgreSQL (recomendado Supabase)

### Pasos para levantar el proyecto
1. **Entorno Virtual**:
   ```bash
   python -m venv .venv
   .\.venv\ idea-activar  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
2. **Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuración**:
   Cree un archivo `.env` basado en `app/config.py` (incluyendo `DATABASE_URL`, `SECRET_KEY`, y credenciales de Supabase).
4. **Base de Datos**:
   ```bash
   alembic upgrade head
   ```
5. **Lanzar Servidor**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🧪 Testing y Calidad

El proyecto cuenta con una suite de pruebas robusta ubicada en `tests/`:
- **Unit Tests**: Pruebas aisladas de servicios y lógica de permisos (ej. `test_permissions.py`).
- **Integration Tests**: Flujos completos que incluyen base de datos (ej. `test_auth_integration.py`).
- **Infraestructura**: Uso de `conftest.py` para fixtures y `factories.py` para generación de datos de prueba.

---

## 📖 Documentación de la API
La API genera documentación automática interactiva gracias a FastAPI:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
