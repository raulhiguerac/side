import uuid
from datetime import datetime

import pytest

from app.core.exceptions.validation import InvalidCursorError
from app.services.search.helpers.feed.encoding import decode_cursor, encode_cursor
from app.services.search.schemas.feed_schemas import FeedCursor


def _make_cursor(position: int = 0) -> FeedCursor:
    return FeedCursor(
        created_at=datetime(2024, 6, 1, 12, 0, 0),
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        position=position,
    )


# ---------------------------------------------------------------------------
# encode_cursor
# ---------------------------------------------------------------------------

def test_encode_cursor_returns_string():
    token = encode_cursor(_make_cursor())
    assert isinstance(token, str)
    assert len(token) > 0


def test_encode_cursor_produces_url_safe_characters():
    token = encode_cursor(_make_cursor())
    assert "+" not in token
    assert "/" not in token


# ---------------------------------------------------------------------------
# decode_cursor
# ---------------------------------------------------------------------------

def test_decode_cursor_roundtrip():
    cursor = _make_cursor(position=42)
    token = encode_cursor(cursor)
    decoded = decode_cursor(token)

    assert decoded.id == cursor.id
    assert decoded.position == cursor.position
    assert decoded.created_at == cursor.created_at


def test_decode_cursor_invalid_base64_raises():
    with pytest.raises(InvalidCursorError):
        decode_cursor("not!!valid!!base64@@")


def test_decode_cursor_valid_base64_but_invalid_json_raises():
    import base64
    bad_token = base64.urlsafe_b64encode(b"not json at all").decode("utf-8")
    with pytest.raises(InvalidCursorError):
        decode_cursor(bad_token)


def test_decode_cursor_valid_json_but_wrong_schema_raises():
    import base64
    import json
    bad_token = base64.urlsafe_b64encode(
        json.dumps({"foo": "bar"}).encode("utf-8")
    ).decode("utf-8")
    with pytest.raises(InvalidCursorError):
        decode_cursor(bad_token)
