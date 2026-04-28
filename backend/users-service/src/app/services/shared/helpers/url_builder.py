from urllib.parse import urlencode, urljoin


def build_redirect_url(
    *,
    front_base_url: str,
    path: str,
    query_params: dict[str, str],
) -> str:
    base = front_base_url.rstrip("/") + "/"
    full_path = path.lstrip("/")
    query = urlencode(query_params)
    return f"{urljoin(base, full_path)}?{query}"

def build_public_url(*, base_url: str, bucket: str, key: str) -> str:
    return f"{base_url.rstrip('/')}/{bucket}/{key.lstrip('/')}"