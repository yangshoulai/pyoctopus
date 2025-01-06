import hashlib
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, wait, Future, ALL_COMPLETED
from enum import Enum
from urllib.parse import urljoin, urlencode, parse_qs, urlparse

import requests

from .reqeust import Request, State as RequestState
from .response import Response
from .site import Site
from .store import Store, memory_store
from .types import Processor, Matcher

_HEADER_COOKIE = 'Cookie'
_HEADER_REFERER = 'Referer'
_HEADER_UA = 'User-Agent'
_DEFAULT_HEADERS = {
    _HEADER_UA: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

_REGEX_REFERER = re.compile(r'^(https?://([^/]+)).*$')


def _generate_request_id(r: Request) -> str:
    parsed_url = urlparse(r.url)
    existing_params = parse_qs(parsed_url.query)
    if r.queries:
        for k, v in r.queries.items():
            q = []
            q.extend(existing_params.get(k, []))
            q.extend(v if v else [])
            q = sorted(q)
            existing_params[k] = q
    url = parsed_url._replace(query=urlencode(
        sorted(existing_params.items()), doseq=True)).geturl()
    if r.data:
        url = f'{url}&{r.data}'
    url = f'{r.method}{url}'
    md5 = hashlib.md5()
    md5.update(url.encode('utf-8'))
    return md5.hexdigest()


class State(Enum):
    INIT = 0
    STARTING = 1
    STARTED = 2
    STOPPING = 3
    STOPPED = 4


class Octopus:
    def __init__(self, store: Store = None,
                 processors: list[tuple[Matcher, Processor]] = None,
                 threads: int = os.cpu_count(),
                 queue_factor: int = 2,
                 sites: list[Site] = None
                 ):
        self._store = store or memory_store()
        self._seeds = []
        self._processors = processors if processors is not None else []
        self._threads = threads
        self._queue_factor = queue_factor
        if sites:
            self._sites = {s.host: s for s in sites}
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(
            self._queue_factor * self._threads)
        self._workers = None
        self._workers_futures = []
        self._boss = None
        self._boss_future = None

        self._state = State.INIT

    def start_async(self, *seeds: Request | str) -> Future[None]:
        if not self._set_state(State.STARTING, State.INIT):
            raise RuntimeError("Octopus is not in INIT state")
        if seeds:
            self._seeds.extend(
                [Request(s) if isinstance(s, str) else s for s in seeds])
        self._state = State.STARTING
        for s in self._seeds:
            self.add(s)
        self._boss = ThreadPoolExecutor(max_workers=1)
        self._workers = ThreadPoolExecutor(max_workers=self._threads)
        self._state = State.STARTED
        self._boss_future = self._boss.submit(self._dispatch)
        logging.info("Octopus started")
        return self._boss_future

    def start(self, *seeds: Request | str):
        self.start_async(*seeds).result()

    def stop(self):
        if not self._set_state(State.STOPPING, State.STARTED):
            raise RuntimeError("Octopus is not in STARTED state")
        wait([self._boss_future, *self._workers_futures],
             return_when=ALL_COMPLETED)
        self._boss.shutdown()
        self._workers.shutdown()
        self._state = State.STOPPED
        logging.info("Octopus stopped")

    def add(self, r: Request, p: Request = None) -> None:
        with self._lock:
            if self._state.value > State.STARTED.value:
                raise RuntimeError("Octopus is not in STARTED state")
        if p is not None:
            r.parent = p.id
            r.depth = p.depth + 1
            if r.inherit:
                r.headers = {**p.headers, **r.headers}
                r.attrs = {**p.attrs, **r.attrs}
            if r.headers.get(_HEADER_REFERER, None) is None:
                m = _REGEX_REFERER.match(p.url)
                if m is not None:
                    r.headers[_HEADER_REFERER] = m.group(1)
            if not r.url.startswith('http'):
                r.url = urljoin(p.url, r.url)
        r.id = _generate_request_id(r)
        r.state = RequestState.WAITING
        r.msg = '等待处理'
        if not self._store.put(r) and not r.repeatable:
            logging.debug(
                f"Can not put [{r}] to store, maybe it has been visited")

    @property
    def state(self):
        with self._lock:
            return self._state

    def _dispatch(self) -> None:
        while True:
            with self._lock:
                if self._state.value >= State.STOPPING.value:
                    break
            self._workers_futures = [
                f for f in self._workers_futures if not f.done()]
            r = self._store.get()
            if r is not None:
                logging.info(f"Take {r}")
                self._semaphore.acquire()
                self._workers_futures.append(
                    self._workers.submit(self._process, r))
            else:
                if len(self._workers_futures) == 0:
                    threading.Thread(target=self.stop).start()

        if self._state.value > State.STARTED.value:
            self._log_undone_tasks()

    def _process(self, r: Request):
        global res
        try:
            site = self._get_site(urlparse(r.url).hostname)
            if site.limiter is not None:
                site.limiter.acquire()
            res = Octopus._download(r, site)
            if res.status != 200:
                raise ValueError(
                    "Bad http status [%s] for [%s]", res.status, r)
            for [m, p] in self._processors:
                if m(res):
                    new_requests = p(res)
                    for req in new_requests:
                        if self._state.value < State.STOPPING.value:
                            self.add(req, r)
            r.msg = '成功处理'
            r.state = RequestState.COMPLETED
            self._store.update_state(r, RequestState.COMPLETED, '成功处理')
        except BaseException as e:
            r.msg = str(e)
            r.state = RequestState.FAILED
            self._store.update_state(r, RequestState.FAILED, str(e))
            logging.exception(f"Process [req = {r}, resp = {res}] error")
        finally:
            self._semaphore.release()

        if self._state.value > State.STARTED.value:
            self._log_undone_tasks()

    def _set_state(self, new_state: State, expected_state: State) -> bool:
        with self._lock:
            if self._state == expected_state:
                self._state = new_state
                logging.debug(
                    f"Octopus state changed from {expected_state} to {new_state}")
                return True
            else:
                return False

    @staticmethod
    def _download(request: Request, site: Site) -> Response:
        h = {**_DEFAULT_HEADERS, **site.headers, **request.headers}
        p = {}
        if site.proxy:
            p = {
                'http': site.proxy,
                'https': site.proxy
            }
        r = requests.request(request.method, request.url, params=request.queries, data=request.data,
                             headers=h, proxies=p)
        _res = Response(request)
        _res.status = r.status_code
        _res.content = r.content
        _res.headers = {k: v for k, v in r.headers.items()}
        _res.encoding = r.encoding
        return _res

    def _get_site(self, host: str) -> Site:
        if host in self._sites:
            return self._sites[host]
        for h, s in self._sites.items():
            if re.match(h.replace("*", ".*"), host):
                return s
        return Site(host)

    def _log_undone_tasks(self):
        undone_count = len(
            [x for x in [self._boss_future, *self._workers_futures] if not x.done()])
        if undone_count > 0:
            logging.info(
                f"Wait for {undone_count} tasks in the queue to complete")


def new(store: Store = None,
        processors: list[tuple[Matcher, Processor]] = None,
        threads: int = os.cpu_count(),
        queue_factor: int = 2,
        sites: list[Site] = None) -> Octopus:
    return Octopus(store=store, processors=processors, threads=threads, queue_factor=queue_factor, sites=sites)
