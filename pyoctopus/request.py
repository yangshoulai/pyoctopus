import json
from enum import Enum
from typing import Any


class State(Enum):
    NEW = 'NEW'
    WAITING = 'WAITING'
    EXECUTING = 'EXECUTING'
    FAILED = 'FAILED'
    COMPLETED = 'COMPLETED'


class Request:
    def __init__(self, url: str, method: str = 'GET',
                 *,
                 queries: dict[str, list[Any] | Any] = None,
                 data: str = None,
                 headers: dict[str, str] = None,
                 priority: int = 0,
                 repeatable: bool = True,
                 attrs: dict[str, Any] = None,
                 inherit: bool = False):
        if not url:
            raise ValueError('url is empty')
        if not method:
            raise ValueError('method is empty')
        if method not in ('GET', 'POST'):
            raise ValueError('method can only be GET or POST')
        self.url = url
        self.method = method
        self.queries = {}
        if queries:
            for k, v in queries.items():
                if isinstance(v, str):
                    self.queries[k] = [str(v)]
        self.data = data
        self.headers = {} if headers is None else headers
        self.priority = priority
        self.repeatable = repeatable
        self.attrs = {} if attrs is None else attrs
        self.inherit = inherit
        self.parent = None
        self.id = None
        self.state = State.NEW
        self.msg = None
        self.depth = 1

    def get_attr(self, name):
        return self.attrs.get(name, None)

    def set_attr(self, name, value):
        self.attrs[name] = value

    def __lt__(self, other):
        return self.priority < other.priority

    def __str__(self):
        return f'{{id={self.id}, url={self.url}, priority={self.priority}, depth={self.depth}}}'

    def to_json(self) -> str:
        return json.dumps({
            'id': self.id,
            'url': self.url,
            'method': self.method,
            'queries': self.queries,
            'data': self.data,
            'headers': self.headers,
            'priority': self.priority,
            'repeatable': self.repeatable,
            'attrs': self.attrs,
            'inherit': self.inherit,
            'parent': self.parent,
            'state': self.state.value,
            'msg': self.msg,
            'depth': self.depth
        })

    @staticmethod
    def from_json(json_str: str) -> 'Request':
        json_object = json.loads(json_str)
        req = Request(json_object['url'])
        req.id = json_object['id']
        req.method = json_object['method']
        req.queries = json_object['queries']
        req.data = json_object['data']
        req.headers = json_object['headers']
        req.priority = json_object['priority']
        req.repeatable = json_object['repeatable']
        req.attrs = json_object['attrs']
        req.inherit = json_object['inherit']
        req.parent = json_object['parent']
        req.state = State(json_object['state'])
        req.msg = json_object['msg']
        req.depth = json_object['depth']
        return req

    __repr__ = __str__


def new(url: str, method: str = 'GET',
        *,
        queries: dict[str, list[Any] | Any] = None,
        data: str = None,
        headers: dict[str, str] = None,
        priority: int = 0,
        repeatable: bool = True,
        attrs: dict[str, Any] = None,
        inherit: bool = False) -> Request:
    return Request(url, method, queries=queries, data=data, headers=headers, priority=priority, repeatable=repeatable,
                   attrs=attrs, inherit=inherit)
