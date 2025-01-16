import os
from typing import List
from urllib.parse import urlparse

from ..request import Request
from ..response import Response
from ..types import Processor


def new(base_dir: str = os.path.expanduser('~/Downloads'), *, sub_dir_attr: str | list[str] = None,
        filename_attr: str = None) -> Processor:
    def process(res: Response) -> List[Request]:
        if sub_dir_attr is not None:
            dir_attrs = sub_dir_attr if isinstance(sub_dir_attr, list) else [sub_dir_attr]
        else:
            dir_attrs = []
        d = os.path.join(base_dir, *[str(res.request.get_attr(attr)) for attr in dir_attrs]) if dir_attrs else base_dir
        n = res.request.get_attr(filename_attr) if filename_attr else None
        if not n:
            disposition = res.headers.get('Content-Disposition', None)
            if disposition:
                if 'filename=' in disposition:
                    filename = disposition.split('filename=')[1]
                    if len(filename) > 2:
                        n = filename[1:-1]
        n = n if n else os.path.basename(urlparse(res.request.url).path)
        if not os.path.exists(d):
            os.makedirs(d)
        file = os.path.join(d, n)
        if os.path.exists(file):
            os.remove(file)
        with open(file, 'wb') as f:
            f.write(res.content)
        return []

    return process
