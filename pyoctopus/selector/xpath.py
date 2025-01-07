from lxml import html

from .selector import Selector
from .. import Response
from ..types import Converter


class Xpath(Selector):
    def __init__(self, expr: str,
                 selector: Selector = None,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        super(Xpath, self).__init__(expr,
                                    selector=selector,
                                    multi=multi,
                                    trim=trim,
                                    filter_empty=filter_empty,
                                    format_str=format_str,
                                    converter=converter)

    def do_select(self, content: str, resp: Response) -> list[str]:
        return [html.tostring(x, encoding=resp.encoding) if isinstance(x, html.HtmlElement) else str(x) for x in
                html.fromstring(content).xpath(self.expr)]


def new(expr: str,
        selector: Selector = None,
        *,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Xpath:
    return Xpath(expr, selector, multi=multi, trim=trim, filter_empty=filter_empty,
                 format_str=format_str,
                 converter=converter)
