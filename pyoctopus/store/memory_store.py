import queue
import threading

from .store import Store
from ..reqeust import Request, State


class _Wrapper:
    def __init__(self, r: Request):
        self.request = r

    def __lt__(self, other):
        return not (self.request < other.request)


class _MemoryStore(Store):
    def __init__(self):
        self._queue = queue.PriorityQueue()
        self._visited = set()
        self._lock = threading.Lock()

    def put(self, r: Request) -> bool:
        with self._lock:
            if r.repeatable or r.id not in self._visited:
                self._visited.add(r.id)
                self._queue.put(_Wrapper(r))
                return True
            return False

    def get(self) -> Request | None:
        try:
            r = self._queue.get(False)
            return r.request if r else None
        except queue.Empty:
            return None

    def update_state(self, r: Request, state: State, msg: str = None):
        r.msg = msg
        r.state = state


def new() -> Store:
    return _MemoryStore()
