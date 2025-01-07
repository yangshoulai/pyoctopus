import logging
from typing import Type, List

from ..reqeust import Request
from ..response import Response
from ..selector import select
from ..types import Collector, Processor, R

_logger = logging.getLogger('pyoctopus.processor.extractor')


def new(result_class: Type[R], collector: Collector = None, *args, **kwargs) -> Processor:
    def process(res: Response) -> List[Request]:
        r, links = select(res.text, res, result_class=result_class, *args, **kwargs)
        if r is not None:
            if collector:
                collector(r)
        else:
            _logger.debug(f'No content found from {res}')
        if not links:
            _logger.debug(f'No links found from {res}')
        return links

    return process
