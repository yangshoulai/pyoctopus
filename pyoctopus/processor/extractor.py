from typing import Type, List

from ..reqeust import Request
from ..response import Response
from ..selector import select
from ..types import Collector, Processor, R


def new(result_class: Type[R], collector: Collector = None, *args, **kwargs) -> Processor:
    def process(res: Response) -> List[Request]:
        r, links = select(res.text, result_class=result_class, *args, **kwargs)
        if collector:
            collector(r)
        return links

    return process
