import curl_cffi
import requests
from ..request import Request
from ..response import Response
from ..site import Site

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def curl_cffi_downloader(request: Request, site: Site) -> Response:
    h = {**_DEFAULT_HEADERS, **site.headers, **request.headers}
    p = {}
    if site.proxy:
        p = {"http": site.proxy, "https": site.proxy}
    r = curl_cffi.request(
        request.method,
        request.url,
        params=request.queries,
        data=request.data,
        headers=h,
        proxies=p,
        timeout=site.timeout,
        impersonate="chrome",
    )
    res = Response(request)
    res.status = r.status_code
    res.content = r.content
    res.headers = {k.lower(): v for k, v in r.headers.items()}
    res.encoding = r.encoding or site.encoding or "utf-8"
    return res


def requests_downloader(request: Request, site: Site) -> Response:
    h = {**_DEFAULT_HEADERS, **site.headers, **request.headers}
    p = {}
    if site.proxy:
        p = {"http": site.proxy, "https": site.proxy}
    r = requests.request(
        request.method,
        request.url,
        params=request.queries,
        data=request.data,
        headers=h,
        proxies=p,
        timeout=site.timeout,
    )
    res = Response(request)
    res.status = r.status_code
    res.content = r.content
    res.headers = {k.lower(): v for k, v in r.headers.items()}
    res.encoding = r.encoding or site.encoding or "utf-8"
    return res
