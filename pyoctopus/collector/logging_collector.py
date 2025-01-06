import logging

from ..types import Collector, R


def new() -> Collector:
    def _collect(r: R) -> None:
        logging.info(str(r))

    return _collect
