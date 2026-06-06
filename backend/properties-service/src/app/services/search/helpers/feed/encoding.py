import json
import base64

from app.services.search.schemas.feed_schemas import FeedCursor

from app.core.exceptions.validation import InvalidCursorError

def encode_cursor(cursor: FeedCursor) -> str:
    next_cursor = json.dumps(cursor.model_dump(mode="json")).encode("utf-8")
    next_cursor_str = base64.urlsafe_b64encode(next_cursor).decode("utf-8")

    return next_cursor_str

def decode_cursor(cursor: str) -> FeedCursor:
    try:
        cursor_encode = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        model = json.loads(cursor_encode.decode("utf-8"))

        return FeedCursor.model_validate(model)
    except Exception as e:
        raise InvalidCursorError()