import re
from urllib.parse import urlparse

from ..types import Matcher


def and_matcher(*matchers: Matcher) -> Matcher:
    return lambda res: all(m(res) for m in matchers)


def or_matcher(*matchers: Matcher) -> Matcher:
    return lambda res: any(m(res) for m in matchers)


def not_matcher(matcher: Matcher) -> Matcher:
    return lambda res: not matcher(res)


def host_matcher(host: str) -> Matcher:
    return lambda res: urlparse(res.request.url).hostname == host


def url_matcher(regex: str) -> Matcher:
    r = re.compile(regex)
    return lambda res: bool(r.match(res.request.url))


def content_type_matcher(regex: str) -> Matcher:
    return header_matcher('Content-Type', regex)


def header_matcher(header: str, regex: str) -> Matcher:
    r = re.compile(regex)
    return lambda res: bool(r.match(res.headers.get(header, '')))


ALL: Matcher = lambda res: True

JSON: Matcher = content_type_matcher(r'.*application/json.*')

HTML: Matcher = content_type_matcher(r'.*text/html.*')

IMAGE: Matcher = content_type_matcher(r'.*image.*')

VIDEO: Matcher = content_type_matcher(r'.*video.*')

PDF: Matcher = content_type_matcher(r'.*application/pdf.*')

WORD: Matcher = content_type_matcher(r'.*application/msword.*')

EXCEL: Matcher = content_type_matcher(r'.*application/vnd.ms-excel.*')

AUDIO: Matcher = content_type_matcher(r'.*audio.*')

OCTET_STREAM = content_type_matcher(r'.*application/octet-stream.*')

MEDIA = or_matcher(IMAGE, VIDEO, AUDIO)
