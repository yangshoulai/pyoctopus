from typing import Any


class Request:
    def __init__(self, url: str, method: str = 'GET',
                 *,
                 queries: dict[str, list[str]] = None,
                 data: str = None,
                 headers: dict[str, str] = None,
                 priority: int = 0,
                 repeatable: bool = True,
                 attrs: dict[str, Any] = None):
        self.url = url
        self.method = method
        self.queries = {} if queries is None else queries
        self.data = data
        self.headers = {} if headers is None else headers
        self.priority = priority
        self.repeatable = repeatable
        self.attrs = {} if attrs is None else attrs
        self.parent = None
        self.id = None

    def get_attr(self, name):
        return self.attrs.get(name, None)

    def set_attr(self, name, value):
        self.attrs[name] = value

    def __lt__(self, other):
        return self.priority < other.priority

    def __str__(self):
        return f'{{id={self.id}, url={self.url}}}'

    __repr__ = __str__


def new(url: str, method: str = 'GET',
        *,
        queries: dict[str, list[str]] = None,
        data: str = None,
        headers: dict[str, str] = None,
        priority: int = 0,
        repeatable: bool = True,
        attrs: dict[str, Any] = None) -> Request:
    return Request(url, method, queries=queries, data=data, headers=headers, priority=priority, repeatable=repeatable,
                   attrs=attrs)
