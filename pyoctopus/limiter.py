import threading
from datetime import datetime, timedelta
from time import sleep


class Limiter:
    def __init__(self, interval_in_seconds: float, capacity: int):
        self._capacity = capacity
        self._interval = interval_in_seconds
        self._count = 0
        self._last_time = datetime.now()
        self._lock = threading.RLock()

    def acquire(self, timeout_milliseconds: int = None) -> bool:
        with self._lock:
            if timeout_milliseconds is None or timeout_milliseconds <= 0:
                return self._acquire()
            else:
                return self._acquire(datetime.now() + timedelta(milliseconds=timeout_milliseconds))

    def _acquire(self, end_time: datetime = None) -> bool:
        now = datetime.now()
        self._count = min(self._capacity,
                          self._count + int((now.timestamp() - self._last_time.timestamp()) / self._interval))
        if self._count > 0:
            self._count = self._count - 1
            self._last_time = now
            return True
        if end_time is None:
            sleep(self._interval - now.timestamp() + self._last_time.timestamp())
            return self._acquire(end_time)
        else:
            if now > end_time:
                return False
            sleep(min(self._interval, self._interval - now.timestamp() + self._last_time.timestamp()))
            return self._acquire(end_time)


def new(interval_in_seconds: float = 1, capacity: int = 1) -> Limiter:
    return Limiter(interval_in_seconds, capacity)
