import logging

from ..types import Collector, R

_logger = logging.getLogger('pyoctopus.collector.logging')


def new() -> Collector:
    def _collect(r: R) -> None:
        _logger.info(str(r))

    return _collect
