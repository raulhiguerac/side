from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI

from apscheduler.schedulers.asyncio import AsyncIOScheduler
# En v3 los triggers se importan así o se pasan como string
from app.workers.keycloak_tasks import run_job

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # 1. Instanciar el scheduler estable
    scheduler = AsyncIOScheduler()
    app.state.scheduler = scheduler

    # 2. Configurar la tarea
    # seconds=900 son 15 minutos
    scheduler.add_job(
        run_job,
        trigger="interval", 
        seconds=900,
        id="kc_compensation",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60
    )

    # 3. Iniciar
    scheduler.start()
    
    yield  # Aquí es donde la app corre
    
    # 4. Apagar al cerrar la app
    scheduler.shutdown()