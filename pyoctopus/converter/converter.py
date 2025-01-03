from datetime import datetime
from typing import List

from ..types import Converter

def int_converter(default_value: int = None) -> Converter:
    return lambda x: int(x) if x else default_value


def float_converter(default_value: int = None) -> Converter:
    return lambda x: float(x) if x else default_value


def bool_converter(true_values: List[str] = None, default_value: int = None) -> Converter:
    if true_values is None:
        true_values = ['true', '1', 'y', 'yes', 'on', 't']
    return lambda x: x.lower() in true_values if x else default_value


def datetime_converter(pattern='%Y-%m-%d %H:%M:%S', default_value: datetime = None) -> Converter:
    return lambda x: datetime.strptime(x, pattern) if x else default_value
