import re

import redis

from .store import Store
from ..request import State, Request


class RedisStore(Store):

    def __init__(self, *, prefix: str = 'pyoctopus', host: str = '127.0.0.1', port: int = 6379, db: int = 0,
                 password: str = None):
        if ':' in prefix:
            raise ValueError('Prefix cannot contain colon')
        self._prefix = prefix
        self._pool = redis.ConnectionPool(host=host, port=port, db=db, password=password)
        self._client = redis.Redis(connection_pool=self._pool)
        self._waiting_priority_pattern = re.compile(f'^{prefix}:waiting:(.*):(.*)$')
        # executing -> waiting
        self._re_waiting()

    def put(self, r: Request) -> bool:
        self._client.set(f'{self._prefix}:all:{r.id}', r.to_json())
        self._client.set(f'{self._prefix}:waiting:{r.priority}:{r.id}', '')
        return True

    def get(self) -> Request | None:
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=f'{self._prefix}:waiting:*', count=20)
            if keys:
                key = sorted([k.decode() for k in keys], reverse=True)[0]
                m = self._waiting_priority_pattern.match(key)
                id = m.group(2)
                req = Request.from_json(self._client.get(f'{self._prefix}:all:{id}'))
                self._client.delete(key)
                self._client.set(f'{self._prefix}:executing:{id}', req.priority)
                return req
            if cursor == 0:
                return None

    def exists(self, id: str) -> bool:
        return self._client.exists(f'{self._prefix}:all:{id}')

    def update_state(self, r: Request, state: State, msg: str = None):
        self._client.set(f'{self._prefix}:all:{r.id}', r.to_json())
        if state == State.COMPLETED:
            self._client.set(f'{self._prefix}:completed:{r.id}', '')
            self._client.delete(f'{self._prefix}:executing:{r.id}')
            self._client.delete(f'{self._prefix}:failed:{r.id}')
        elif state == State.FAILED:
            self._client.set(f'{self._prefix}:failed:{r.id}', r.priority)
            self._client.delete(f'{self._prefix}:executing:{r.id}')
            self._client.delete(f'{self._prefix}:completed:{r.id}')
        elif state == State.WAITING:
            self._client.delete(f'{self._prefix}:failed:{r.id}')
            self._client.delete(f'{self._prefix}:executing:{r.id}')
            self._client.delete(f'{self._prefix}:completed:{r.id}')
            self._client.set(f'{self._prefix}:waiting:{r.priority}:{r.id}', '')
        else:
            raise ValueError(f'Invalid state: {state}')

    def reply_failed(self) -> int:
        cursor = 0
        count = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=f'{self._prefix}:failed:*', count=100)
            count += len(keys)
            for k in keys:
                self._client.set(f'{self._prefix}:waiting:{self._client.get(k)}:{k.split(":")[-1]}', '')
                self._client.delete(k)
            if cursor == 0:
                break
        return count

    def get_statistics(self) -> (int, int, int, int, int):
        return (self._get_key_size(f'{self._prefix}:all:*'),
                self._get_key_size(f'{self._prefix}:waiting:*'),
                self._get_key_size(f'{self._prefix}:executing:*'),
                self._get_key_size(f'{self._prefix}:completed:*'),
                self._get_key_size(f'{self._prefix}:failed:*'))

    def _get_key_size(self, key: str) -> int:
        cursor = 0
        count = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=key, count=100)
            count += len(keys)
            if cursor == 0:
                break
        return count

    def _re_waiting(self):
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=f'{self._prefix}:executing:*', count=100)
            for k in keys:
                priority = self._client.get(k)
                self._client.set(f'{self._prefix}:waiting:{priority}:{k.split(":")[-1]}', '')
                self._client.delete(k)
            if cursor == 0:
                break


def new(*, prefix: str = 'pyoctopus', host: str = '127.0.0.1', port: int = 6379, db: int = 0,
        password: str = None) -> RedisStore:
    return RedisStore(prefix=prefix, host=host, port=port, db=db, password=password)
