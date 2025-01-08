import queue

from .store import Store
from ..reqeust import Request, State


class _Wrapper:
    def __init__(self, id: str, priority: int):
        self.id = id
        self.priority = priority

    def __lt__(self, other):
        return not (self.priority < other.priority)


class _MemoryStore(Store):
    def __init__(self):
        self._queue = queue.PriorityQueue()
        self._all: dict[str, Request] = {}
        self._fails = set()
        self._executing = set()
        self._completed = set()

    def put(self, r: Request) -> bool:
        self._all[r.id] = r
        self._queue.put(_Wrapper(r.id, r.priority))
        return True

    def get(self) -> Request | None:
        try:
            r = self._queue.get(False)
            req = self._all[r.id] if r else None
            if req:
                req.state = State.EXECUTING
                req.msg = '正在处理'
                self._executing.add(r.id)
            return req
        except queue.Empty:
            return None

    def update_state(self, r: Request, state: State, msg: str = None):
        if state == State.COMPLETED:
            self._completed.add(r.id)
            self._fails.discard(r.id)
            self._executing.discard(r.id)
        elif state == State.FAILED:
            self._fails.add(r.id)
            self._completed.discard(r.id)
            self._executing.discard(r.id)
        elif state == State.WAITING:
            self._completed.discard(r.id)
            self._executing.discard(r.id)
            self._fails.discard(r.id)
            self._queue.put(_Wrapper(r.id, r.priority))
        else:
            raise ValueError(f'Invalid state: {state}')

    def exists(self, id: str) -> bool:
        return id in self._all

    def reply_failed(self) -> int:
        fails = [self._all[f] for f in self._fails]
        for fail in fails:
            fail.state = State.WAITING
            fail.msg = '等待处理'
            self.update_state(fail, State.WAITING, '等待处理')
        return len(fails)

    def get_statistics(self) -> (int, int, int, int, int):
        return len(self._all), self._queue.qsize(), len(self._executing), len(self._completed), len(self._fails)


def new() -> Store:
    return _MemoryStore()
