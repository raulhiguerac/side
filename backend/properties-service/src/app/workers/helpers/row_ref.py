def row_ref(row: dict) -> str:
    """Human-readable identifier for a raw CSV row, used in error traces so an
    admin can find the offending row without opening the file. Uses `.get` with
    a `?` fallback because the referenced fields may be exactly the ones missing."""
    return f"{row.get('email', '?')} @ {row.get('lat', '?')},{row.get('lon', '?')}"
