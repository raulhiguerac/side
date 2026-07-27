import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import BulkJobNotFoundError
from app.core.exceptions.storage import StorageMisconfiguredError
from app.schemas.principal import Principal
from app.workers.bulk_create_properties_worker import BulkCreatePropertiesWorker

PRINCIPAL = Principal(sub=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
JOB_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

HEADER = (
    "external_id,area_m2,cuartos,estrato,tipo,parqueaderos,banios,piso,precio,"
    "precio_admin,tipo_propiedad,lat,lon,antiguedad,descripcion,image_urls,email\n"
)
VALID_ROW = "A-{n},80,3,4,venta,1,2,3,350000000,0,apartamento,4.65,-74.05,1 a 8 años,,,owner@test.com\n"


def _csv(rows: int = 1) -> bytes:
    return (HEADER + "".join(VALID_ROW.format(n=i) for i in range(rows))).encode()


@pytest.fixture
def uow():
    u = MagicMock()
    u.commit = AsyncMock()
    u.rollback = AsyncMock()
    u.bulk_jobs = MagicMock()
    u.bulk_jobs.get_by_id.return_value = MagicMock(storage_key="admin/file.csv")
    return u


@pytest.fixture
def worker(monkeypatch, uow):
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BUCKET_BULK_PROPERTIES", "bulk-bucket")
    return BulkCreatePropertiesWorker(
        uow=uow,
        catalog=AsyncMock(),
        users=AsyncMock(),
        storage=MagicMock(),
    )


def _patch_stream(payload: bytes):
    async def _iter(*, storage, bucket, key):
        import csv
        import io

        reader = csv.DictReader(io.StringIO(payload.decode()))
        for row in reader:
            yield row

    return patch("app.workers.bulk_create_properties_worker.iter_csv_rows", new=_iter)


def _patch_threadpool():
    async def _run(fn):
        return fn()

    return patch(
        "app.workers.bulk_create_properties_worker.run_in_threadpool",
        new=AsyncMock(side_effect=_run),
    )


def _patch_chunk(inserted: int = 1, errors=None):
    return patch(
        "app.workers.bulk_create_properties_worker.process_chunk",
        new_callable=AsyncMock,
        return_value=(inserted, errors or []),
    )


# ---------------------------------------------------------------------------
# Wiring: the job row drives the run
# ---------------------------------------------------------------------------

async def test_reads_the_storage_key_from_the_job_row(worker, uow):
    uow.bulk_jobs.get_by_id.return_value = MagicMock(storage_key="admin/some-file.csv")
    seen = {}

    async def _iter(*, storage, bucket, key):
        seen["bucket"], seen["key"] = bucket, key
        for _ in ():
            yield

    with _patch_threadpool(), patch(
        "app.workers.bulk_create_properties_worker.iter_csv_rows", new=_iter
    ), patch("app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock):
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    assert seen == {"bucket": "bulk-bucket", "key": "admin/some-file.csv"}


async def test_unknown_job_fails_the_run(worker, uow):
    uow.bulk_jobs.get_by_id.return_value = None

    with _patch_threadpool(), patch(
        "app.workers.bulk_create_properties_worker.mark_job_failed", new_callable=AsyncMock
    ) as mark, pytest.raises(BulkJobNotFoundError):
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    mark.assert_awaited_once()


def test_refuses_to_start_without_a_bucket(monkeypatch, uow):
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BUCKET_BULK_PROPERTIES", "")
    with pytest.raises(StorageMisconfiguredError):
        BulkCreatePropertiesWorker(uow=uow, catalog=AsyncMock(), users=AsyncMock(), storage=MagicMock())


# ---------------------------------------------------------------------------
# Outcome is written back to the job, never returned
# ---------------------------------------------------------------------------

async def test_finalizes_the_job_with_the_accumulated_errors(worker):
    with _patch_threadpool(), _patch_stream(_csv(1)), _patch_chunk(inserted=1), patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ) as finalize:
        result = await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    assert result is None  # nobody is listening; the row is the output
    finalize.assert_awaited_once()
    assert finalize.await_args.kwargs["job_id"] == JOB_ID


async def test_a_crash_marks_the_job_failed_and_reraises(worker):
    with _patch_threadpool(), _patch_stream(_csv(1)), patch(
        "app.workers.bulk_create_properties_worker.process_chunk",
        new_callable=AsyncMock,
        side_effect=Exception("catalog down"),
    ), patch(
        "app.workers.bulk_create_properties_worker.mark_job_failed", new_callable=AsyncMock
    ) as mark, patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ) as finalize, pytest.raises(Exception, match="catalog down"):
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    mark.assert_awaited_once()
    finalize.assert_not_awaited()


# ---------------------------------------------------------------------------
# Row validation happens before chunking
# ---------------------------------------------------------------------------

async def test_an_invalid_row_is_reported_with_its_csv_line(worker):
    bad = HEADER + "A-1,80,3,4,venta,1,2,3,350000000,0,apartamento,NOT_A_LAT,-74.05,x,,,o@test.com\n"

    with _patch_threadpool(), _patch_stream(bad.encode()), _patch_chunk(inserted=0), patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ) as finalize:
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    errors = finalize.await_args.kwargs["errors"]
    assert len(errors) == 1
    assert errors[0].line == 2  # header is line 1


async def test_a_row_missing_external_id_is_rejected(worker):
    header_no_ext = HEADER.replace("external_id,", "")
    body = header_no_ext + "80,3,4,venta,1,2,3,350000000,0,apartamento,4.65,-74.05,x,,,o@test.com\n"

    with _patch_threadpool(), _patch_stream(body.encode()), _patch_chunk(inserted=0), patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ) as finalize:
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    assert len(finalize.await_args.kwargs["errors"]) == 1


async def test_a_valid_row_survives_validation(worker):
    with _patch_threadpool(), _patch_stream(_csv(3)), _patch_chunk(inserted=3) as chunk, patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ) as finalize:
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    assert finalize.await_args.kwargs["errors"] == []
    assert len(chunk.await_args.args[0]) == 3


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

async def test_the_tail_below_the_chunk_size_is_still_processed(worker):
    with _patch_threadpool(), _patch_stream(_csv(10)), _patch_chunk(inserted=10) as chunk, patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ):
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    chunk.assert_awaited_once()


async def test_chunks_are_capped_and_the_email_cache_is_shared(worker, monkeypatch):
    monkeypatch.setattr("app.workers.bulk_create_properties_worker._CHUNK_SIZE", 4)

    with _patch_threadpool(), _patch_stream(_csv(10)), _patch_chunk(inserted=4) as chunk, patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ):
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    sizes = [len(call.args[0]) for call in chunk.await_args_list]
    assert sizes == [4, 4, 2]

    caches = [call.kwargs["email_cache"] for call in chunk.await_args_list]
    assert all(cache is caches[0] for cache in caches)


async def test_an_empty_file_finalizes_without_touching_the_db(worker):
    with _patch_threadpool(), _patch_stream(HEADER.encode()), _patch_chunk() as chunk, patch(
        "app.workers.bulk_create_properties_worker.finalize_job", new_callable=AsyncMock
    ) as finalize:
        await worker.execute(principal=PRINCIPAL, job_id=JOB_ID)

    chunk.assert_not_awaited()
    finalize.assert_awaited_once()
    assert finalize.await_args.kwargs["errors"] == []


# ---------------------------------------------------------------------------
# Owner resolution delegates to the gateway
# ---------------------------------------------------------------------------

async def test_process_users_batch_calls_the_gateway_with_a_list(worker):
    worker.users.resolve_accounts.return_value = []

    await worker._process_users_batch({"a@test.com", "b@test.com"})

    emails = worker.users.resolve_accounts.await_args.kwargs["emails"]
    assert sorted(emails) == ["a@test.com", "b@test.com"]
