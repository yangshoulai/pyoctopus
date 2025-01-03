from .limiter import Limiter


class Site:
    def __init__(self,
                 host: str,
                 *,
                 limiter: Limiter = None,
                 headers: dict[str, str] = None,
                 proxy: str = None):
        self._host = host
        self._limiter = limiter
        self._headers = headers if headers is not None else {}
        self._proxy = proxy

    @property
    def host(self):
        return self._host

    @property
    def limiter(self):
        return self._limiter

    @property
    def headers(self):
        return self._headers

    @property
    def proxy(self):
        return self._proxy


def new(host: str,
        *,
        limiter: Limiter = None,
        headers: dict[str, str] = None,
        proxy: str = None) -> Site:
    return Site(host, limiter=limiter, headers=headers, proxy=proxy)
