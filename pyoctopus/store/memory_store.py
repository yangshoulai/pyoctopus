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
        self._all = {}
        self._fails = []
        self._completed = set()

    def put(self, r: Request) -> bool:
        self._all[r.id] = r
        self._queue.put(_Wrapper(r.id, r.priority))
        return True

    def get(self) -> Request | None:
        try:
            r = self._queue.get(False)
            return self._all[r.id] if r else None
        except queue.Empty:
            return None

    def update_state(self, r: Request, state: State, msg: str = None):
        if state == State.COMPLETED:
            self._completed.add(r.id)
            self._fails = [f for f in self._fails if f != r.id]
        elif state == State.FAILED:
            self._fails.append(r.id)
            self._completed.discard(r.id)
        elif state == State.WAITING:
            self._completed.discard(r.id)
            self._fails = [f for f in self._fails if f != r.id]
            self._queue.put(_Wrapper(r.id, r.priority))
        else:
            raise ValueError(f'Invalid state: {state}')

    def exists(self, id: str) -> bool:
        return id in self._all

    def get_fails(self, page: int = 1, page_size: int = 100) -> list[Request]:
        return [self._all[f] for f in self._fails[page_size * (page - 1):page_size * page]]

    def get_statistics(self) -> (int, int, int, int):
        return len(self._all), self._queue.qsize(), len(self._completed), len(self._fails)


def new() -> Store:
    return _MemoryStore()
