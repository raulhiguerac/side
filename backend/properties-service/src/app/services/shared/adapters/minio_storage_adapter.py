import asyncio
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.integrations.storage.minio.storage import StorageClient
from app.services.shared.ports.storage import StoragePort


class MinioStorageAdapter(StoragePort):
    def __init__(self, client: StorageClient) -> None:
        self._client = client

    async def generate_presigned_put_url(self, *, bucket: str, key: str, ttl: int) -> str:
        return await run_in_threadpool(
            self._client.generate_presigned_put_url,
            bucket=bucket,
            key=key,
            ttl=ttl,
        )

    async def generate_presigned_put_urls(self, *, bucket: str, keys: list[str], ttl: int) -> list[str]:
        return await asyncio.gather(*[
            run_in_threadpool(
                partial(self._client.generate_presigned_put_url, bucket=bucket, key=key, ttl=ttl)
            )
            for key in keys
        ])
