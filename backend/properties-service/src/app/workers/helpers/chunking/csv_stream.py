import csv
from typing import AsyncIterator

from app.services.shared.ports.storage import StoragePort

NEWLINE = b"\n"


async def chunk_file(storage: StoragePort, *, bucket: str, key: str) -> AsyncIterator[str]:
    partial_chunk = b""

    async for chunk in storage.chunk_file(bucket=bucket, key=key):
        data = partial_chunk + chunk
        last_newline = data.rfind(NEWLINE)

        result = data[: last_newline + 1].decode("utf-8")
        if result:
            yield result

        partial_chunk = data[last_newline + 1 :]

    if partial_chunk:
        yield partial_chunk.decode("utf-8")


async def iter_csv_rows(storage: StoragePort, *, bucket: str, key: str) -> AsyncIterator[dict]:
    """
    Yields one resolved dict per CSV row, built from the header captured once
    at the start of the file.

    csv.reader doesn't error on a buffer cut mid-quote — it silently closes
    the field at EOF and truncates the value (verified empirically). Fields
    like `descripcion` can contain literal newlines inside quotes, spanning
    more than one physical line and even more than one chunk_file() yield.
    So we only hand csv.reader a buffer once the count of `"` in it is even
    (no quote left open) — that's the only way to guarantee it never sees a
    truncated quoted field.
    """
    header: list[str] | None = None
    pending = ""
    open_quotes = 0

    async for text in chunk_file(storage=storage, bucket=bucket, key=key):
        pending += text
        open_quotes += text.count('"')

        if open_quotes % 2 != 0:
            continue  # quote still open, spans into the next chunk — keep buffering

        rows = list(csv.reader(pending.splitlines(keepends=True)))
        pending = ""
        open_quotes = 0

        if header is None:
            if not rows:
                continue
            header = rows.pop(0)

        for row in rows:
            yield dict(zip(header, row))
