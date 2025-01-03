from typing import TypeVar, Callable, Any

from . import Request
from .response import Response

R = TypeVar('R', bound=[type])

Converter = TypeVar('Converter', bound=[Callable[[str], Any]])

Matcher = TypeVar('Matcher', bound=[Callable[[Response], bool]])

Processor = TypeVar('Processor', bound=[Callable[[Response], list[Request]]])

Collector = TypeVar('Collector', bound=[Callable[[R], None]])
