from .request import Request


class Response:
    def __init__(self,
                 request: Request,
                 *,
                 status: int = 0,
                 content: bytes = None,
                 headers: dict[str, str] = None,
                 encoding: str = 'utf-8'
                 ):
        self.request = request
        self.content = content
        self.status = status
        self.content = content
        self.headers = headers
        self.encoding = encoding
        self._text = None
        self._parsed = False

    @property
    def text(self):
        if self._parsed:
            return self._text
        self._text = self.content.decode(self.encoding)
        self._parsed = True
        return self._text

    def __str__(self):
        return f'{{request={self.request}, status={self.status}, length={len(self.content)}, encoding={self.encoding}}}'

    __repr__ = __str__


def new(request: Request,
        status: int = 0,
        content: bytes = None,
        headers: dict[str, str] = None,
        encoding: str = 'utf-8') -> Response:
    return Response(request, status=status, content=content, headers=headers, encoding=encoding)
