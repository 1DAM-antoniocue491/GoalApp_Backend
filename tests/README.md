# Tests del Backend

Este directorio contiene todos los tests automatizados para el backend de GoalApp.

## Estructura

```
tests/
├── __init__.py                  # Inicialización del paquete
├── conftest.py                  # Fixtures y configuración global
├── test_auth.py                 # Tests de autenticación
├── test_usuarios.py             # Tests de usuarios
├── test_roles.py                # Tests de roles
├── test_ligas.py                # Tests de ligas
├── test_liga_configuracion.py   # Tests de configuración de liga
├── test_equipos.py              # Tests de equipos
├── test_jugadores.py            # Tests de jugadores
├── test_partidos.py             # Tests de partidos
├── test_eventos.py              # Tests de eventos de partido
├── test_convocatorias.py        # Tests de convocatorias
├── test_notificaciones.py       # Tests de notificaciones
├── test_imagenes.py             # Tests de gestión de imágenes
├── test_permissions.py          # Tests de permisos por rol
└── test_public.py               # Tests de endpoints públicos
```

## Requisitos

Instalar las dependencias de testing:

```bash
cd backend
pip install pytest pytest-cov httpx
```

## Ejecutar Tests

### Todos los tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con más detalle
pytest -v

# Ejecutar mostrando prints
pytest -s

# Ejecutar sin warnings
pytest --disable-warnings
```

### Tests específicos

```bash
# Un archivo específico
pytest tests/test_auth.py

# Una clase específica
pytest tests/test_auth.py::TestLogin

# Un test específico
pytest tests/test_auth.py::TestLogin::test_login_correcto

# Varios archivos
pytest tests/test_auth.py tests/test_usuarios.py

# Tests que coincidan con un patrón
pytest -k "login"
pytest -k "crear_usuario"
```

### Con cobertura

```bash
# Ver cobertura en terminal
pytest --cov=app

# Ver cobertura detallada
pytest --cov=app --cov-report=term-missing

# Generar reporte HTML
pytest --cov=app --cov-report=html

# Abrir reporte HTML
# Windows:
start htmlcov/index.html
# Linux/Mac:
open htmlcov/index.html
```

### Tests marcados

```bash
# Solo tests de autenticación
pytest -m auth

# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Excluir tests lentos
pytest -m "not slow"
```

## Fixtures Disponibles

Los fixtures están definidos en `conftest.py` y se pueden usar en cualquier test:

### Base de datos y cliente

| Fixture | Descripción |
|---------|-------------|
| `db` | Sesión de base de datos SQLite en memoria (se limpia después de cada test) |
| `client` | Cliente HTTP para hacer peticiones a la API |

### Usuarios

| Fixture | Descripción |
|---------|-------------|
| `usuario_ejemplo` | Usuario de prueba básico |
| `usuario2_ejemplo` | Segundo usuario de prueba |
| `token_usuario` | Token JWT para usuario_ejemplo |
| `headers_auth` | Headers con Authorization Bearer |
| `usuario_admin` | Usuario con rol admin |
| `token_admin` | Token JWT para usuario_admin |
| `headers_admin` | Headers con autorización de admin |

### Roles

| Fixture | Descripción |
|---------|-------------|
| `rol_admin` | Rol de administrador |
| `rol_coach` | Rol de entrenador |
| `rol_player` | Rol de jugador |

### Entidades

| Fixture | Descripción |
|---------|-------------|
| `liga_ejemplo` | Liga de prueba |
| `liga2_ejemplo` | Segunda liga de prueba |
| `liga_configuracion_ejemplo` | Configuración de liga de prueba |
| `equipo_ejemplo` | Equipo de prueba |
| `equipo2_ejemplo` | Segundo equipo de prueba |
| `jugador_ejemplo` | Jugador de prueba |
| `partido_ejemplo` | Partido de prueba |
| `notificacion_ejemplo` | Notificación de prueba |

### Datos

| Fixture | Descripción |
|---------|-------------|
| `datos_usuario_nuevo` | Diccionario con datos para crear usuario |
| `datos_liga_nueva` | Diccionario con datos para crear liga |
| `datos_equipo_nuevo` | Diccionario con datos para crear equipo |

## Escribir Nuevos Tests

### Estructura básica

```python
# tests/test_ejemplo.py
import pytest

class TestMiFuncionalidad:
    """Tests para mi funcionalidad."""

    def test_caso_exitoso(self, client):
        """Descripción del test."""
        response = client.get("/api/v1/mi-endpoint/")

        assert response.status_code == 200
        assert "datos" in response.json()

    def test_caso_error(self, client):
        """Test de caso de error."""
        response = client.get("/api/v1/mi-endpoint/999")

        assert response.status_code == 404
```

### Usar fixtures

```python
class TestMiEndpoint:
    def test_con_usuario_autenticado(self, client, headers_auth):
        """Test con usuario autenticado."""
        response = client.get(
            "/api/v1/protegido/",
            headers=headers_auth
        )

        assert response.status_code == 200

    def test_sin_autenticacion(self, client):
        """Test sin autenticación."""
        response = client.get("/api/v1/protegido/")

        assert response.status_code == 401

    def test_con_admin(self, client, headers_admin):
        """Test con usuario admin."""
        response = client.post(
            "/api/v1/admin/recurso/",
            headers=headers_admin,
            json={"nombre": "Nuevo"}
        )

        assert response.status_code == 201
```

### Crear datos de prueba

```python
def test_crear_recurso(self, client, headers_admin, liga_ejemplo):
    """Test que necesita una liga existente."""
    response = client.post(
        "/api/v1/equipos/",
        headers=headers_admin,
        json={
            "nombre": "Nuevo Equipo",
            "id_liga": liga_ejemplo.id_liga
        }
    )

    assert response.status_code == 201
```

## Base de Datos de Prueba

Los tests usan una base de datos **SQLite en memoria** que:

1. Se crea antes de cada test
2. Se destruye después de cada test
3. Está aislada de la base de datos de desarrollo

Esto significa que:
- Los tests son rápidos
- No afectan a datos reales
- Cada test empieza con una base limpia

## Tests de Permisos

Para probar que un endpoint requiere ciertos permisos:

```python
class TestPermisos:
    def test_endpoint_requiere_admin(self, client, token_usuario):
        """Verificar que el endpoint requiere rol admin."""
        response = client.delete(
            "/api/v1/ligas/1",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )

        assert response.status_code == 403
```

## Tests de Autenticación

Para probar endpoints que requieren autenticación:

```python
class TestAutenticacion:
    def test_sin_token(self, client):
        """Sin token debe devolver 401."""
        response = client.get("/api/v1/usuarios/me")
        assert response.status_code == 401

    def test_con_token(self, client, token_usuario):
        """Con token válido debe devolver 200."""
        response = client.get(
            "/api/v1/usuarios/me",
            headers={"Authorization": f"Bearer {token_usuario}"}
        )
        assert response.status_code == 200
```

## Ejecutar Tests en CI/CD

```yaml
# Ejemplo para GitHub Actions
- name: Run tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml
```

## Solución de Problemas

### Error: "Module not found"

```bash
# Asegúrate de estar en el directorio correcto
cd backend

# Instala las dependencias
pip install -r requirements.txt
pip install pytest pytest-cov httpx
```

### Error: "Database locked"

Los tests usan SQLite en memoria, este error no debería ocurrir. Si pasa:

```bash
# Limpiar cache de pytest
pytest --cache-clear
```

### Tests lentos

```bash
# Ejecutar tests en paralelo
pip install pytest-xdist
pytest -n auto
```

## Cobertura de Código

```bash
# Ver resumen de cobertura
pytest --cov=app --cov-report=term-missing

# Ejemplo de salida:
# Name                    Stmts   Miss  Cover   Missing
# -----------------------------------------------------
# app/main.py                45      2    96%   23-24
# app/api/routers/          120     10    92%
# app/api/services/         200     15    93%
# -----------------------------------------------------
# TOTAL                     365     27    93%
```

##Buenas Prácticas

1. **Un test, una funcionalidad**: Cada test debe probar una sola cosa
2. **Nombres descriptivos**: `test_login_correcto` en lugar de `test_login`
3. **Usar fixtures**: No crear datos manualmente en cada test
4. **Assert claros**: `assert response.status_code == 200` es más claro que `assert response.ok`
5. **Tests independientes**: Cada test debe funcionar solo, sin depender de otros