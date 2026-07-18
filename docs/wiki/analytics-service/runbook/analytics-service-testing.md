---
title: Testing — analytics-service unit suite
status: stable
last-verified: 2026-07-13
owners: [analytics-service]
related:
  - "[[analytics-service-local-dev]]"
  - "[[analytics-service-kafka-consumer]]"
  - "[[analytics-service-prediction]]"
sources:
  - ../../../sources/analytics-service/2026-05-25-unit-test-suite.md
---

## TL;DR

63 tests unitarios en `tests/unit/`, todos pasando. Cubre el dominio prediction completo (adapter, UCs, helper) y el worker Kafka (types, consumer). Patrones clave: `_fake_threadpool` para UCs con `run_in_threadpool`, `make_consumer` factory para el consumer, `AsyncMock` vs `MagicMock` según si el método es async o sync.

## Setup

Pytest vive bajo `[project.optional-dependencies] dev` — no se instala con `uv sync` por defecto:

```bash
uv sync --extra dev
uv run python -m pytest tests/unit/
```

`asyncio_mode = "auto"` en `pyproject.toml` — `@pytest.mark.asyncio` es opcional en tests async.

## Layout de los tests

```
tests/unit/
├── services/prediction/
│   ├── adapters/
│   │   └── test_avm_model_adapter.py       # AVMModelAdapter — float cast, excludes property_id
│   ├── helpers/
│   │   └── test_record_builder.py          # build_prediction_record — field mapping, audit
│   └── use_cases/
│       ├── test_online_prediction.py       # OnlinePrediction UC — rollback, error wrapping, logger
│       └── test_batch_prediction.py        # BatchPrediction UC — bulk, fallback row-by-row, savepoints
└── workers/listing_created/
    ├── conftest.py                         # fixtures compartidas del consumer
    ├── helpers/
    │   └── test_types.py                   # WorkerMessage — strict fields, extra forbidden
    └── test_consumer.py                    # ListingConsumer — config, poll, produce, serialize, consume_batch
```

## Patrones de mocking

### UCs con `run_in_threadpool`

Los UCs llaman `run_in_threadpool(partial(...))` para operaciones bloqueantes. En tests, se reemplaza con un fake que llama la función directamente:

```python
async def _fake_threadpool(func):
    return func()

with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
    response = await uc.execute(principal=PRINCIPAL, req=REQ)
```

El path del patch debe apuntar al módulo que importa `run_in_threadpool`, no a `fastapi.concurrency`.

### AsyncMock vs MagicMock

Los métodos del UoW tienen dos naturalezas distintas:

| Método | Naturaleza | Mock |
|--------|-----------|------|
| `uow.commit()`, `uow.rollback()`, `uow.begin_nested()`, `uow.rollback_to_savepoint()` | `async def` | `AsyncMock` |
| `uow.prediction.add()`, `uow.prediction.batch_add()` | `def` (sync, SQLModel session) | `MagicMock` |

### `BatchPredictionResult` — instanciar, no mockear

```python
from app.services.prediction.schemas.prediction import BatchPredictionResult

def _make_result(*, predictions=(), failed=()):
    return BatchPredictionResult(predictions=list(predictions), failed=list(failed))

uc.execute.return_value = _make_result(predictions=[(PROP_ID, 500.0)])
```

## Consumer fixture

El consumer fixture en `tests/unit/workers/listing_created/conftest.py` parchea `Consumer` y `Producer` de confluent-kafka durante el `__init__`. Los mock instances persisten después del `with` block y se acceden via `c.consumer` / `c.producer`:

```python
def make_consumer(monkeypatch, uc=None, env_overrides=None):
    for k, v in {**_ENV, **(env_overrides or {})}.items():
        monkeypatch.setenv(k, v)
    if uc is None:
        uc = AsyncMock()
    with (
        patch("app.workers.listing_created.consumer.Consumer"),
        patch("app.workers.listing_created.consumer.Producer"),
    ):
        c = ListingConsumer(uc=uc)
    c.producer.flush.return_value = 0
    return c, uc
```

### Secuencia de poll

```python
def poll_seq(consumer, *msgs):
    consumer.consumer.poll.side_effect = list(msgs) + [None]
```

Siempre añadir `None` al final — el loop drena hasta `msg is None`, y si `side_effect` se agota sin `None` lanza `StopIteration`.

### Mensajes de prueba

```python
def good_msg(data: str):           # UTF-8 válido
    msg = MagicMock()
    msg.error.return_value = None
    msg.value.return_value = data.encode("utf-8")
    ...

def bad_utf8_msg():                # bytes inválidos → UnicodeDecodeError natural
    msg = MagicMock()
    msg.value.return_value = b"\xff\xfe"
    ...
```

Usar bytes reales `b"\xff\xfe"` — `.decode("utf-8")` lanza `UnicodeDecodeError` nativamente, y `base64.b64encode()` sobre los mismos bytes sigue funcionando (lo que usa el consumer para el rejected payload).

### Tests de `consume_batch`

Parchear `_poll_batch` directamente para aislar la lógica de orquestación del loop de poll:

```python
with patch.object(c, "_poll_batch", return_value=([VALID_MSG], [])):
    await c.consume_batch()
```

`patch.object` funciona sobre métodos estáticos — añade un atributo de instancia que sombrea el atributo de clase. `partial(self.produce, ...)` toma el mock de instancia correctamente.

## Claims

- Tests unitarios se encuentran en `tests/unit/` — 63 tests, todos pasan con `uv run python -m pytest tests/unit/` ([pyproject.toml](backend/analytics-service/pyproject.toml)).
- `pytest` y `pytest-asyncio` están bajo `[project.optional-dependencies] dev` en `pyproject.toml` — requieren `uv sync --extra dev` para instalarse ([pyproject.toml](backend/analytics-service/pyproject.toml)).
- `asyncio_mode = "auto"` está configurado en `[tool.pytest.ini_options]` — `@pytest.mark.asyncio` no es obligatorio ([pyproject.toml](backend/analytics-service/pyproject.toml)).
- `pythonpath = ["src"]` está en `[tool.pytest.ini_options]` — no hace falta `PYTHONPATH=src` al correr pytest ([pyproject.toml](backend/analytics-service/pyproject.toml)).
- Los métodos de repo del UoW (`add`, `batch_add`) son síncronos (SQLModel session) — se mockean con `MagicMock`, no `AsyncMock` ([ports/unit_of_work.py](backend/analytics-service/src/app/services/prediction/ports/unit_of_work.py)).
- `make_consumer` parchea `Consumer` y `Producer` de `confluent_kafka` durante el `__init__` — las instancias mock persisten en `c.consumer` y `c.producer` tras salir del contexto ([tests/unit/workers/listing_created/conftest.py](backend/analytics-service/tests/unit/workers/listing_created/conftest.py)).
- `poll.side_effect` debe terminar con `None` — el loop de `_poll_batch` drena hasta que `poll()` retorna `None` ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
