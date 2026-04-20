"""
Migración 002: Hacer opcionales id_entrenador e id_delegado en equipos

Esta migración permite crear equipos sin especificar entrenador o delegado.
El sistema asignará automáticamente el usuario que crea el equipo como
entrenador y delegado por defecto.

Para ejecutar:
    python -m migrations.run 002_make_equipo_entrenador_delegado_nullable
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Ejecuta la migración para hacer nullable id_entrenador e id_delegado."""

    if not DATABASE_URL:
        print("ERROR: DATABASE_URL no configurada en .env")
        return False

    # Para SQLite, la sintaxis es diferente
    if DATABASE_URL.startswith("sqlite"):
        print("INFO: SQLite no soporta ALTER COLUMN directamente.")
        print("INFO: En SQLite, los campos ya pueden ser NULL si no hay datos existentes.")
        print("INFO: Saltando migración para SQLite.")
        return True

    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            print("Ejecutando migración 002...")

            # Hacer id_entrenador nullable
            conn.execute(text("""
                ALTER TABLE equipos
                ALTER COLUMN id_entrenador DROP NOT NULL
            """))
            print("  - id_entrenador ahora es nullable")

            # Hacer id_delegado nullable
            conn.execute(text("""
                ALTER TABLE equipos
                ALTER COLUMN id_delegado DROP NOT NULL
            """))
            print("  - id_delegado ahora es nullable")

            conn.commit()
            print("Migración 002 completada exitosamente!")
            return True

    except Exception as e:
        print(f"ERROR en migración 002: {e}")
        return False


def run_migration_sqlite(db_path: str):
    """
    Para SQLite, necesitamos recrear la tabla porque no soporta ALTER COLUMN.
    Solo ejecutar si la base de datos está vacía o para desarrollo.
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar si hay datos
    cursor.execute("SELECT COUNT(*) FROM equipos")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"WARNING: Hay {count} equipos en la base de datos.")
        print("WARNING: No se puede modificar la tabla con datos existentes en SQLite.")
        print("WARNING: Considera usar MySQL/PostgreSQL para producción.")
        conn.close()
        return False

    # Recrear tabla con columnas nullable
    cursor.execute("DROP TABLE IF EXISTS equipos")
    cursor.execute("""
        CREATE TABLE equipos (
            id_equipo INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            ciudad VARCHAR(255),
            escudo VARCHAR(255),
            colores VARCHAR(50),
            id_liga INTEGER NOT NULL,
            id_entrenador INTEGER,
            id_delegado INTEGER,
            estadio VARCHAR(255),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (id_liga) REFERENCES ligas(id_liga),
            FOREIGN KEY (id_entrenador) REFERENCES usuarios(id_usuario),
            FOREIGN KEY (id_delegado) REFERENCES usuarios(id_usuario)
        )
    """)

    conn.commit()
    conn.close()
    print("Migración 002 completada para SQLite (tabla recreada)")
    return True


if __name__ == "__main__":
    run_migration()
