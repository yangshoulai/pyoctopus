from .selector import Selector
from .. import Response
from ..types import Converter


class Header(Selector):
    def __init__(self,
                 expr: str,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        super(Header, self).__init__(expr,
                                     multi=multi,
                                     trim=trim,
                                     filter_empty=filter_empty,
                                     format_str=format_str,
                                     converter=converter)

    def do_select(self, content: str, resp: Response) -> list[str]:
        attr = resp.request.headers.get(self.expr, None)
        if attr is None:
            return []
        return [str(c) for c in attr] if isinstance(attr, list) else [str(attr)]


def new(name: str,
        *,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Header:
    return Header(name,
                  multi=multi,
                  trim=trim,
                  filter_empty=filter_empty,
                  format_str=format_str,
                  converter=converter)
