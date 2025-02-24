import logging
from abc import abstractmethod
from typing import List, Any

from .. import Request, Response
from ..types import Converter, Terminable
from ..types import R

PROP_LINKS = '__result_links__'
_logger = logging.getLogger('pyoctopus.selector')


class Link:
    def __init__(self,
                 selector: 'Selector',
                 method: str = 'GET',
                 *,
                 queries: dict[str, list[str]] = None,
                 data: str = None,
                 headers: dict[str, str] = None,
                 priority: int = 0,
                 repeatable: bool = True,
                 attr_props: list[str] = None,
                 inherit: bool = False,
                 terminable: Terminable = None):
        self.selector = selector
        self.method = method
        self.queries = {} if queries is None else queries
        self.data = data
        self.headers = {} if headers is None else headers
        self.priority = priority
        self.repeatable = repeatable
        self.attr_props = attr_props
        self.inherit = inherit
        self.terminable = terminable


class Selector:
    def __init__(self,
                 expr: str,
                 selector: 'Selector' = None,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        if selector and not isinstance(selector, Selector):
            raise ValueError('selector must be a Selector')
        self.expr = expr
        self.selector = selector
        self.multi = multi
        self.trim = trim
        self.filter_empty = filter_empty
        self.format_str = format_str
        self.converter = converter

    def select(self, content: str, resp: Response) -> str | list[str]:
        try:
            selected = []
            if content and self.selector:
                content = self.selector.select(content, resp)
            if content and self.expr is not None:
                if isinstance(content, list):
                    for c in content:
                        selected.append(*self.do_select(c, resp))
                else:
                    selected = [*self.do_select(content, resp)]

            selected = selected if self.multi else ([selected[0]] if len(selected) > 0 else [])

            if selected and self.trim:
                selected = [x.strip() for x in selected]

            if self.filter_empty:
                selected = [x for x in selected if x]

            if self.format_str:
                selected = [self.format_str.format(x) for x in selected]

            if self.converter:
                if self.multi:
                    selected = [self.converter(x) for x in selected]
                else:
                    selected = [self.converter(selected[0]) if len(selected) > 0 else self.converter(None)]
            return selected if self.multi else (selected[0] if len(selected) > 0 else None)
        except BaseException as e:
            _logger.error(f"failed to select value from [{content} with selector [{self}]")
            raise e

    @abstractmethod
    def do_select(self, content: str, resp: Response) -> List[str]:
        pass

    def __str__(self):
        return f'{self.__class__.__name__}{{expr={self.expr}}}'

    __repr__ = __str__


class Embedded:
    def __init__(self, selector: Selector, embedded_class: type[R], *args, **kwargs):
        self.selector = selector
        self.target = embedded_class
        self.args = args
        self.kwargs = kwargs

    def select(self, content: str, resp: Response, links: list[Request] = None) -> R | list[R]:
        if links is None:
            links = []
        selected = self.selector.select(content, resp)
        if isinstance(selected, list):
            results = []
            for x in selected:
                s = select(x, resp, self.target, *self.args, **self.kwargs)
                results.append(s[0])
                links.extend(s[1])
            return results
        s = select(selected, resp, self.target, *self.args, **self.kwargs)
        links.extend(s[1])
        return s[0]


def embedded(selector: Selector, embedded_class: type[R], *args, **kwargs) -> Embedded:
    return Embedded(selector, embedded_class, *args, **kwargs)


def _get_type_selectors_links(cls: type) -> (dict[str, Selector | Embedded], List[Any]):
    selectors = {}
    links = []
    for t in [*cls.__bases__, cls]:
        for k, v in t.__dict__.items():
            if isinstance(v, Selector) or isinstance(v, Embedded):
                selectors[k] = v
        links.extend(_get_links(t))
    return selectors, links


def select(content: str, resp: Response, result_class: type, links: list[Request] = None, *args, **kwargs) -> (
        R, list[Request]):
    r = result_class(*args, **kwargs)
    _selectors, _links = _get_type_selectors_links(type(r))
    if links is None:
        links = []
    for key, value in _selectors.items():
        if isinstance(value, Selector):
            r.__dict__[key] = value.select(content, resp)
        elif isinstance(value, Embedded):
            r.__dict__[key] = value.select(content, resp, links)

    for link in _links:
        if link.terminable and link.terminable(r, content, resp):
            continue
        requests = []
        l = link.selector.select(content, resp)
        if l:
            if isinstance(l, list):
                requests.extend(l)
            else:
                requests.append(l)
            new_requests = [Request(x,
                                    link.method,
                                    queries=link.queries,
                                    data=link.data,
                                    headers=link.headers,
                                    priority=link.priority,
                                    repeatable=link.repeatable,
                                    inherit=link.inherit) for x in requests]
            if link.attr_props:
                for attr_prop in link.attr_props:
                    if attr_prop in r.__dict__:
                        for new_request in new_requests:
                            new_request.set_attr(attr_prop, r.__dict__[attr_prop])

            links.extend(new_requests)
    return r, links


def link(selector: Selector, method: str = 'GET',
         *,
         queries: dict[str, list[str]] = None,
         data: str = None,
         headers: dict[str, str] = None,
         priority: int = 0,
         repeatable: bool = True,
         attr_props: list[str] = None,
         inherit: bool = False,
         terminable: Terminable = None) -> Link:
    return Link(selector,
                method,
                queries=queries,
                data=data,
                headers=headers,
                priority=priority,
                repeatable=repeatable,
                attr_props=attr_props,
                inherit=inherit,
                terminable=terminable)


_LINKS: dict[type, list[Link]] = {}


def _get_links(cls: type) -> list[Link]:
    return _LINKS.get(cls, [])


def hyperlink(*links: Link):
    def decorator(cls):
        _LINKS[cls] = [*links]
        return cls

    return decorator
