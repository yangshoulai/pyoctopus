from .selector import Selector
from ..types import Converter


class Regex(Selector):
    def __init__(self,
                 expr: str,
                 group: int = 0,
                 selector: Selector = None,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        super(Regex, self).__init__(expr,
                                    selector=selector,
                                    multi=multi,
                                    trim=trim,
                                    filter_empty=filter_empty,
                                    format_str=format_str,
                                    converter=converter)
        self.group = group

    def do_select(self, content: str) -> str | list[str]:
        import re
        matches = re.finditer(self.expr, content)
        return [x.group(self.group) for x in matches]


def new(expr: str,
        group: int = 0,
        selector: Selector = None,
        *,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Regex:
    return Regex(expr,
                 group,
                 selector,
                 multi=multi,
                 trim=trim,
                 filter_empty=filter_empty,
                 format_str=format_str,
                 converter=converter)
