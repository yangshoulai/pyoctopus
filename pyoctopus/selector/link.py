import functools

from .selector import Selector, R, PROP_LINKS
from .. import Terminable


class Link:
    def __init__(self,
                 selector: Selector,
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


class Hyperlink:
    def __init__(self, links: list[Link], result_class: R):
        self.links = links
        self.result_class = result_class

    def __call__(self, *args, **kwargs):
        r = self.result_class(*args, **kwargs)
        r.__dict__[PROP_LINKS] = self.links
        return r


def hyperlink(*links: Link):
    return functools.partial(Hyperlink, links)


def link(selector: Selector, method: str = 'GET',
         *,
         queries: dict[str, list[str]] = None,
         data: str = None,
         headers: dict[str, str] = None,
         priority: int = 0,
         repeatable: bool = True,
         attr_props: list[str] = None,
         inherit: bool = False,
         terminable: Terminable) -> Link:
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
