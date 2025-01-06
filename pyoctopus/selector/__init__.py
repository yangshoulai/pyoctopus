from .attr import new as attr
from .css import new as css
from .header import new as header
from .id import new as id
from .json import new as json
from .link import link, hyperlink
from .query import new as query
from .regex import new as regex
from .selector import embedded, select
from .url import new as url
from .xpath import new as xpath

__all__ = [
    'embedded',
    'select',
    'css',
    'xpath',
    'regex',
    'json',
    'attr',
    'url',
    'link',
    'hyperlink',
    'query',
    'header',
    'id'
]
