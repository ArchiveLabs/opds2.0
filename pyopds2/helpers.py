from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse


def build_url(base_url: str, params: dict[str, str] | None = None) -> str:
    if not params:
        return base_url

    url_parts = list(urlparse(base_url))
    query = dict(parse_qsl(url_parts[4]))  # preserve existing query params
    query.update(params)
    url_parts[4] = urlencode(query, doseq=True)  # doseq=True supports lists

    return urlunparse(url_parts)
