import urllib
from urllib.parse import urlencode

from .selector import Selector
from .. import Response
from ..types import Converter


class Url(Selector):
    def __init__(self,
                 url_decode: bool = False,
                 url_encode: bool = False,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        super(Url, self).__init__('',
                                  multi=multi,
                                  trim=trim,
                                  filter_empty=filter_empty,
                                  format_str=format_str,
                                  converter=converter)
        self.encode = url_encode
        self.decode = url_decode

    def do_select(self, content: str, resp: Response) -> list[str]:
        r = resp.request.url
        if self.encode:
            r = urllib.parse.quote(r)
        if self.decode:
            r = urllib.parse.unquote(r)
        return [r]


def new(url_decode: bool = False,
        url_encode: bool = False,
        *,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Url:
    return Url(
        url_decode=url_decode,
        url_encode=url_encode,
        multi=multi,
        trim=trim,
        filter_empty=filter_empty,
        format_str=format_str,
        converter=converter)
