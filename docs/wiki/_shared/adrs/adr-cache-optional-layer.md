---
title: ADR-0005 — Cache como capa opcional; degradación silenciosa a DB
status: stable
last-verified: 2026-06-09
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[catalog-service-architecture]]"
  - "[[properties-service-architecture]]"
  - "[[analytics-service-architecture]]"
sources: [../../sources/_shared/2026-06-09-mvp-audit-scores.md]
---

## TL;DR

Redis es una capa de optimización, no una dependencia crítica. Si Redis cae o lanza una excepción, todos los servicios degradan silenciosamente a lectura directa de DB — el request no falla. Esto se implementa con `except Exception: pass` alrededor de las operaciones de cache.

## Contexto

Todos los microservicios del monorepo usan Redis para cache-aside (lectura) e invalidación (escritura). Durante la auditoría de MVP (2026-06-09) se identificó que el patrón `except Exception: pass` en bloques de cache es intencional y correcto, no deuda técnica.

## Decisión

Las operaciones de cache (lectura y escritura) se envuelven en `try/except Exception: pass`. Si Redis no responde:

- **Cache read miss**: el servicio continúa y hace la query a DB normalmente.
- **Cache write fail**: el servicio retorna el resultado correcto al cliente; la entrada simplemente no queda cacheada. La próxima request irá a DB de nuevo hasta que Redis vuelva.
- **Cache invalidation fail**: el dato puede quedar stale en cache hasta que expire el TTL natural. Aceptable: el TTL es la red de seguridad.

```python
# Patrón correcto — cache read
try:
    cached = await cache.get_json(key=key)
    if cached:
        return deserialize(cached)
except Exception:
    pass  # Redis caído → continúa a DB

result = fetch_from_db()

# Patrón correcto — cache write
try:
    await cache.set_json(key=key, value=result.model_dump(), ttl=TTL)
except Exception:
    pass  # No cachear no es un error del request
```

## Alternativas consideradas

- **Raise en cache fail**: haría que Redis fuera un punto único de falla. Un pico de carga o reinicio de Redis tumbaría la API entera aunque la DB esté sana.
- **Circuit breaker**: más correcto a largo plazo, pero agrega complejidad. Para MVP, el `except pass` cumple el mismo objetivo de no propagar el fallo.

## Consecuencias

- **Positivo**: Redis puede reiniciarse o fallar sin downtime observable.
- **Positivo**: código simple, sin dependencias extra.
- **Negativo**: si Redis cae, la DB absorbe toda la carga. El sistema degrada en rendimiento, no en disponibilidad — aceptable si la DB tiene capacidad.
- **Negativo**: un fallo silencioso de Redis en cache invalidation puede dejar datos stale. Los TTLs de cada servicio (1 día para geo_catalog, 30 días para entidades admin) son la red de seguridad.
- **A futuro**: migrar a circuit breaker cuando haya observabilidad — sin métricas de hit rate de cache, el circuit breaker no añade valor.

## Claims

- Todos los servicios del monorepo usan `except Exception: pass` en operaciones de cache — es patrón deliberado, no deuda ([catalog-service](backend/catalog-service/src/app/services/geo_catalog/), [properties-service](backend/properties-service/src/app/services/search/helpers/feed/ads.py), [analytics-service](backend/analytics-service/src/app/)).
- Un fallo de Redis no propaga un error HTTP al cliente en ningún servicio del monorepo.
- Los TTLs configurados en `settings.py` de cada servicio actúan como red de seguridad contra datos stale por fallo de invalidación.
