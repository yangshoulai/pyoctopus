from .selector import Selector
from .. import Response
from ..types import Converter
from bs4 import BeautifulSoup


class Css(Selector):
    def __init__(self,
                 expr: str,
                 attr=None,
                 text=False,
                 selector:
                 Selector = None,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        super(Css, self).__init__(expr,
                                  selector=selector,
                                  multi=multi,
                                  trim=trim,
                                  filter_empty=filter_empty,
                                  format_str=format_str,
                                  converter=converter)
        self.attr = attr
        self.text = text

    def do_select(self, content: str, resp: Response) -> list[str]:
        html = BeautifulSoup(content, 'lxml')
        return [(x.attrs[self.attr] if self.attr else (x.text if self.text else x.decode())) for x in
                html.select(self.expr)]


def new(expr: str,
        attr=None,
        text=False,
        selector: Selector = None,
        *,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Css:
    return Css(expr,
               attr,
               text,
               selector,
               multi=multi,
               trim=trim,
               filter_empty=filter_empty,
               format_str=format_str,
               converter=converter)
