import threading
from datetime import datetime
from time import sleep


class Limiter:
    def __init__(self, capacity: int, interval_in_seconds: float):
        self._capacity = capacity
        self._interval = interval_in_seconds
        self._count = 0
        self._last_time = datetime.now().timestamp()
        self._lock = threading.RLock()

    def acquire(self):
        with self._lock:
            now = datetime.now().timestamp()
            self._count = min(self._capacity, self._count + int((now - self._last_time) / self._interval))
            if self._count > 0:
                self._count = self._count - 1
                self._last_time = now
            else:
                sleep(self._interval - now + self._last_time)
                self.acquire()


def new(capacity: int = 1, interval_in_seconds: float = 1) -> Limiter:
    return Limiter(capacity, interval_in_seconds)
