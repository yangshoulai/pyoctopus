from .selector import embedded, select

from .css import new as css

from .xpath import new as xpath

from .regex import new as regex

from .json import new as json

from .link import link, hyperlink

__all__ = [
    'embedded',
    'select',
    'css',
    'xpath',
    'regex',
    'json',
    'link',
    'hyperlink'
]
