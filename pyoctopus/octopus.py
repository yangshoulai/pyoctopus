import hashlib
import logging
import os
import queue
import re
import threading
from concurrent.futures import ThreadPoolExecutor, wait, Future, ALL_COMPLETED
from enum import Enum
from urllib.parse import urljoin, urlencode, parse_qs, urlparse

import curl_cffi.requests as curl_cffi
import requests

from .request import Request, State as RequestState
from .response import Response
from .site import Site
from .store import Store, memory_store
from .types import Processor, Matcher, Downloader

_HEADER_COOKIE = 'Cookie'
_HEADER_REFERER = 'Referer'
_HEADER_UA = 'User-Agent'
_DEFAULT_HEADERS = {
    _HEADER_UA: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

_REGEX_REFERER = re.compile(r'^(https?://([^/]+)).*$')

_logger = logging.getLogger('pyoctopus')


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
    def __init__(self, downloader: Downloader = Downloader.REQUESTS, store: Store = None,
                 processors: list[tuple[Matcher, Processor]] = None,
                 threads: int = os.cpu_count(),
                 queue_factor: int = 2,
                 sites: list[Site] = None,
                 retries: int = 1,
                 ):
        self.downloader = downloader or Downloader.REQUESTS
        self._store = store or memory_store()
        self._seeds = []
        self._processors = processors if processors is not None else []
        self._threads = threads
        self._queue_factor = queue_factor
        if sites:
            self._sites = {s.host: s for s in sites}
        self.retries = retries
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(self._queue_factor * self._threads)
        self._workers = None
        self._workers_futures = []
        self._boss = None
        self._boss_future = None
        self._queue = queue.Queue()
        self._state = State.INIT

    def start_async(self, *seeds: Request | str) -> Future[None]:
        if not self._set_state(State.STARTING, State.INIT):
            raise RuntimeError("Pyoctopus is not in INIT state")
        self._state = State.STARTING
        self._seeds.extend([Request(s) if isinstance(s, str) else s for s in seeds])
        for seed in self._seeds:
            self._add(seed)
        self._boss = ThreadPoolExecutor(max_workers=1, thread_name_prefix="boss")
        self._workers = ThreadPoolExecutor(max_workers=self._threads, thread_name_prefix="worker")
        self._boss_future = self._boss.submit(self._dispatch)
        _logger.info("Pyoctopus started")
        self._state = State.STARTED
        return self._boss_future

    def start(self, *seeds: Request | str):
        self.start_async(*seeds).result()

    def stop(self):
        if not self._set_state(State.STOPPING, State.STARTED):
            raise RuntimeError("Pyoctopus is not in STARTED state")
        wait([self._boss_future, *self._workers_futures], return_when=ALL_COMPLETED)
        self._boss.shutdown()
        self._workers.shutdown()
        self._state = State.STOPPED
        stat = self._store.get_statistics()
        _logger.info(
            f"Pyoctopus stats: all = {stat[0]}, waiting = {stat[1]}, executing = {stat[2]}, completed = {stat[3]}, failed = {stat[4]}")
        _logger.info("Pyoctopus stopped")

    def add(self, r: Request) -> None:
        with self._lock:
            if self._state.value > State.STARTED.value:
                raise RuntimeError(f"Pyoctopus is in {self._state} state")
        self._add(r)

    def _add(self, r: Request, p: Request = None) -> None:
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

        def _r():
            if r.repeatable or not self._store.exists(r.id):
                if not self._store.put(r):
                    _logger.warning(f"Can not put [{r}] to store")

        self._queue.put(_r)

    @property
    def state(self):
        with self._lock:
            return self._state

    def _dispatch(self) -> None:
        while True:
            has_queued_tasks = False
            while True:
                try:
                    r = self._queue.get(False)
                    if r is not None:
                        has_queued_tasks = True
                        r()
                    else:
                        break
                except queue.Empty:
                    break
            self._workers_futures = [f for f in self._workers_futures if not f.done()]

            with self._lock:
                if self._state.value >= State.STOPPING.value:
                    if not has_queued_tasks and len(self._workers_futures) == 0:
                        break
                else:
                    r = self._store.get()
                    if r is not None:
                        _logger.info(f"Take {r}")
                        self._semaphore.acquire()
                        self._workers_futures.append(self._workers.submit(self._process, r))
                    if r is None and len(self._workers_futures) == 0 and not has_queued_tasks:
                        if not self._retry_fails():
                            _logger.info("No more tasks found, pyoctopus will stop")
                            threading.Thread(target=self.stop, name="StopThread").start()
                            break
        if self._state.value > State.STARTED.value:
            self._log_undone_tasks()

    def _retry_fails(self) -> bool:
        has_fails = False
        if self.retries > 0:
            count = self._store.reply_failed()
            if count > 0:
                has_fails = True
                _logger.info(f"[{self.retries}] Retry {count} failed requests")
            self.retries = self.retries - 1
        return has_fails

    def _process(self, r: Request):
        res = None
        try:
            site = self._get_site(urlparse(r.url).hostname)
            if site.limiter is not None:
                site.limiter.acquire()
            res = self._download(r, site)
            if res.status != 200:
                raise ValueError(f"Bad http status [{res.status}] for [{r}]")
            for [m, p] in self._processors:
                if m and m(res):
                    for req in p(res):
                        self._add(req, r)
            r.msg = '成功处理'
            r.state = RequestState.COMPLETED
            self._queue.put(lambda: self._store.update_state(r, RequestState.COMPLETED, '成功处理'))
        except BaseException as e:
            r.msg = str(e)
            r.state = RequestState.FAILED
            self._queue.put(lambda: self._store.update_state(r, RequestState.FAILED, r.msg))
            _logger.error(f"Process [req = {r}, resp = {res}] error\n{r.msg}", exc_info=True)
        finally:
            self._semaphore.release()

        if self._state.value > State.STARTED.value:
            self._log_undone_tasks()

    def _set_state(self, new_state: State, expected_state: State) -> bool:
        with self._lock:
            if self._state == expected_state:
                self._state = new_state
                _logger.debug(f"Pyoctopus state changed from {expected_state} to {new_state}")
                return True
            else:
                return False

    def _download(self, request: Request, site: Site) -> Response:
        try:
            h = {**_DEFAULT_HEADERS, **site.headers, **request.headers}
            p = {}
            if site.proxy:
                p = {
                    'http': site.proxy,
                    'https': site.proxy
                }
            if self.downloader == Downloader.REQUESTS:
                r = requests.request(request.method,
                                     request.url,
                                     params=request.queries,
                                     data=request.data,
                                     headers=h,
                                     proxies=p,
                                     timeout=site.timeout)
            else:
                r = curl_cffi.request(request.method,
                                      request.url,
                                      params=request.queries,
                                      data=request.data,
                                      headers=h,
                                      proxies=p,
                                      timeout=site.timeout,
                                      impersonate="chrome")
            _res = Response(request)
            _res.status = r.status_code
            _res.content = r.content
            _res.headers = {k.lower(): v for k, v in r.headers.items()}
            _res.encoding = r.encoding or site.encoding or 'utf-8'
            return _res
        except BaseException as e:
            raise RuntimeError(str(e))

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
            _logger.info(f"Wait for {undone_count} tasks in the queue to complete")


def new(downloader: Downloader = Downloader.REQUESTS, store: Store = None,
        processors: list[tuple[Matcher, Processor]] = None,
        threads: int = os.cpu_count(),
        queue_factor: int = 2,
        sites: list[Site] = None,
        retries: int = 1) -> Octopus:
    return Octopus(downloader=downloader,
                   store=store,
                   processors=processors,
                   threads=threads,
                   queue_factor=queue_factor,
                   sites=sites,
                   retries=retries)
