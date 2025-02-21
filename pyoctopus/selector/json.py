import json as j

from jsonpath_ng import parse

from .selector import Selector
from .. import Response
from ..types import Converter


class Json(Selector):
    def __init__(self,
                 expr: str,
                 selector: Selector = None,
                 *,
                 multi=False,
                 trim=True,
                 filter_empty=True,
                 format_str: str = None,
                 converter: Converter = None):
        super(Json, self).__init__(expr,
                                   selector=selector,
                                   multi=multi,
                                   trim=trim,
                                   filter_empty=filter_empty,
                                   format_str=format_str,
                                   converter=converter)
        self._parser = parse(self.expr)

    def do_select(self, content: str, resp: Response) -> list[str]:
        matches = self._parser.find(j.loads(content))
        return [(x.value if isinstance(x.value, str) else j.dumps(x.value)) if x.value is not None else '' for x in
                matches]


def new(expr: str,
        selector: Selector = None,
        *,
        multi=False,
        trim=True,
        filter_empty=True,
        format_str: str = None,
        converter: Converter = None) -> Json:
    return Json(expr,
                selector,
                multi=multi,
                trim=trim,
                filter_empty=filter_empty,
                format_str=format_str,
                converter=converter)
