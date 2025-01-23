from enum import Enum
from typing import TypeVar, Callable, Any

from .site import Site

from .request import Request
from .response import Response

R = TypeVar("R", bound=[type])

Converter = TypeVar("Converter", bound=[Callable[[str], Any]])

Matcher = TypeVar("Matcher", bound=[Callable[[Response], bool]])

Downloader = TypeVar("Downloader", bound=[Callable[[Request, Site], Response]])

Processor = TypeVar("Processor", bound=[Callable[[Response], list[Request]]])

Collector = TypeVar("Collector", bound=[Callable[[R], None]])

Terminable = TypeVar("Terminable", bound=[Callable[[R, str, Response], bool]])
