from unittest.mock import MagicMock

from app.workers.helpers.chunking.csv_stream import iter_csv_rows

HEADER = "external_id,precio,descripcion\n"


def _storage(*chunks: bytes):
    async def _chunk_file(*, bucket, key):
        for chunk in chunks:
            yield chunk

    storage = MagicMock()
    storage.chunk_file = _chunk_file
    return storage


async def _rows(*chunks: bytes) -> list[dict]:
    return [row async for row in iter_csv_rows(storage=_storage(*chunks), bucket="b", key="k")]


async def test_maps_each_line_onto_the_header():
    rows = await _rows((HEADER + "A-1,100,casa\nA-2,200,lote\n").encode())

    assert rows == [
        {"external_id": "A-1", "precio": "100", "descripcion": "casa"},
        {"external_id": "A-2", "precio": "200", "descripcion": "lote"},
    ]


async def test_header_is_read_once_not_repeated_per_chunk():
    rows = await _rows((HEADER + "A-1,100,casa\n").encode(), b"A-2,200,lote\n")

    assert [row["external_id"] for row in rows] == ["A-1", "A-2"]


async def test_a_row_split_across_chunks_is_reassembled():
    rows = await _rows((HEADER + "A-1,10").encode(), b"0,casa\n")

    assert rows == [{"external_id": "A-1", "precio": "100", "descripcion": "casa"}]


async def test_a_quoted_field_containing_a_newline_stays_one_row():
    body = HEADER + 'A-1,100,"linea uno\nlinea dos"\n'
    rows = await _rows(body.encode())

    assert len(rows) == 1
    assert rows[0]["descripcion"] == "linea uno\nlinea dos"


async def test_a_quoted_field_spanning_two_chunks_is_not_truncated():
    """csv.reader silently truncates a field left open at EOF, so the buffer is
    only handed over once the quote count is even."""
    rows = await _rows(
        (HEADER + 'A-1,100,"empieza aqui').encode(),
        b' y termina alla"\nA-2,200,corto\n',
    )

    assert rows[0]["descripcion"] == "empieza aqui y termina alla"
    assert rows[1]["descripcion"] == "corto"


async def test_a_quoted_field_containing_commas_is_one_field():
    rows = await _rows((HEADER + 'A-1,100,"casa, lote, finca"\n').encode())

    assert rows[0]["descripcion"] == "casa, lote, finca"


async def test_a_file_with_only_a_header_yields_nothing():
    assert await _rows(HEADER.encode()) == []


async def test_a_final_line_without_a_trailing_newline_is_still_read():
    rows = await _rows((HEADER + "A-1,100,casa").encode())

    assert len(rows) == 1
    assert rows[0]["external_id"] == "A-1"
