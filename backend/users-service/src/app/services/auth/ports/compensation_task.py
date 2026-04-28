from typing import Protocol

from app.services.auth.schemas.compensation import CreateKcCompensationTask


class CompensationTaskRepository(Protocol):
    async def add(self, cmd: CreateKcCompensationTask) -> None: ...