---
name: Partidos Con Equipos Duplicate Alias Fix
description: Fix del endpoint /partidos/ligas/{id}/con-equipos por duplicate alias en SQL join
type: feedback
---

El endpoint `GET /api/v1/partidos/ligas/{id}/con-equipos` daba 500 Internal Server Error por un error de SQL duplicate alias.

**Causa:** En `partido_service.py`, la función `obtener_partidos_con_equipos` usaba `EquipoVisitante = Equipo` que no crea un alias SQL real, causando que SQLAlchemy genere dos JOINs a la misma tabla `equipos` sin alias distintos.

**Error:** `psycopg2.errors.DuplicateAlias: table name "equipos" specified more than once`

**Solución:** Usar `aliased(Equipo)` para ambos joins (local y visitante), igual que hacen las demás funciones del mismo archivo.

**Archivo:** `app/api/services/partido_service.py`, función `obtener_partidos_con_equipos` (líneas ~156-168)

**Por qué:** `aliased()` crea un alias SQL real que SQLAlchemy puede distinguir en el query generado. Una asignación Python simple (`EquipoVisitante = Equipo`) solo crea otra referencia a la misma clase, no un alias de tabla.

**How to apply:** Si ves "duplicate alias" o "table specified more than once" en errores SQL de joins múltiples a la misma tabla, usa `aliased(Model)` para cada referencia.
