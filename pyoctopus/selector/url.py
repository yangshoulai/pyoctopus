from .selector import Selector
from .. import Response
from ..types import Converter


class Url(Selector):
    def __init__(self,
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

    def do_select(self, content: str, resp: Response) -> list[str]:
        return [resp.request.url]


def new(*,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Url:
    return Url(
        multi=multi,
        trim=trim,
        filter_empty=filter_empty,
        format_str=format_str,
        converter=converter)
