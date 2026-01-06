def get_keycloak_status(exc: Exception) -> int | None:
    if hasattr(exc, "response_code"):
        return exc.response_code
    if hasattr(exc, "response_status"):
        return exc.response_status
    return None

def get_keycloak_error_text(exc: Exception) -> str:
    parts = []

    msg = getattr(exc, "error_message", None)
    if msg:
        parts.append(str(msg))

    body = getattr(exc, "response_body", None)
    if body:
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", errors="ignore")
        parts.append(str(body))

    return " ".join(parts).lower()
