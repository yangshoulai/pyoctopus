import os
from typing import List
from urllib.parse import urlparse

from ..reqeust import Request
from ..response import Response
from ..types import Processor


def new(base_dir: str = os.path.expanduser('~/Downloads'), *, sub_dir_attr: str = None,
        filename_attr: str = None) -> Processor:
    def process(res: Response) -> List[Request]:
        d = os.path.join(base_dir, res.request.get_attr(sub_dir_attr)) if sub_dir_attr else base_dir
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
