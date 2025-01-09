import os
import re

import pyoctopus
import sample_logging
from pyoctopus import Response, Request

sample_logging.setup()


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath('//figure/a/@href', multi=True), repeatable=False, priority=2)
)
class AlbumList:
    pass


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath('//a[@class="page-numbers"]/@href', multi=True), repeatable=False, priority=2)
)
class AlbumDetails:
    pass


def resolve_img_urls(res: Response) -> list[Request]:
    name = pyoctopus.xpath('//h3/text()').select(res.text, res)
    selected = pyoctopus.xpath('//p/a[not(@target)]/@href', multi=True).select(res.text, res)
    return [pyoctopus.request(replace_url(s), priority=3, attrs={'name': name}, repeatable=False) for s in selected]


def replace_url(u: str) -> str:
    u = u.replace('https://i0.wp.com/pic.4khd.com', 'https://img.xxtt.info')
    if '?w=5555555555' in u:
        u = re.sub(r'\?w=1300', '', u)
        u = re.sub(r's0-rw', '', u)
        u = re.sub(r'img.xxtt.info/-', 'lh5.ggpht.com/-', u)
    u = re.sub(r'AsHYQ', 'AsYHQ', u)
    u = re.sub(r'l/AAA', 'I/AAA', u)
    u = re.sub(r'img.xxtt.info/-', 'i0.wp.com/yt4.googleusercontent.com/-', u)
    u = re.sub(r'resize=500%2C687', 'esize=850%2C1158', u)
    u = re.sub(r'_t.webp', '.webp', u)
    u = re.sub(r'_m.webp', '.webp', u)
    u = re.sub(r'_n.webp', '.webp', u)
    u = re.sub(r'_z.webp', '.webp', u)
    u = re.sub(r'_b.webp', '.webp', u)
    u = re.sub(r'img.xxtt.info/super', 'i0.wp.com/imgsrc.baidu.com/forum', u)
    return u


def get_all_pages(res: Response) -> list[Request]:
    if 'query-3-page' in res.request.url:
        selected = pyoctopus.xpath('(//a[@class="page-numbers"]/@href)[last()]', multi=False).select(res.text, res)
        max_page = int(selected.split('=')[1])
        if max_page > 1:
            return [pyoctopus.request(f'{selected.split("=")[0]}={page}') for page in range(2, max_page + 1)]
    else:
        selected = pyoctopus.xpath('(//a[@class="page-numbers"]/text())[last()]', multi=False).select(res.text, res)
        max_page = int(selected)
        if max_page > 1:
            url_prefix = re.sub(r'/page/\d+', '/page', res.request.url)
            return [pyoctopus.request(f'{url_prefix}/{page}') for page in range(2, max_page + 1)]

    return []


if __name__ == '__main__':
    seed = 'https://sjurj.xxtt.info/search/jvid/page/1'
    proxy = 'http://127.0.0.1:7890'
    sites = [
        pyoctopus.site('sjurj.xxtt.info', proxy=proxy, limiter=pyoctopus.limiter(0.25)),
        pyoctopus.site('*.4khd.*', proxy=proxy, limiter=pyoctopus.limiter(0.25)),
        pyoctopus.site('*.wp.com', proxy=proxy, limiter=pyoctopus.limiter(0.25))
    ]
    store = pyoctopus.store.sqlite_store(os.path.expanduser('~/Downloads/pyoctopus.db'), table='xxtt')
    processors = [
        (pyoctopus.or_matcher(pyoctopus.url_matcher(r'^.*/pages/.*\?query-3-page=1$'),
                              pyoctopus.url_matcher(r'^.*/search/.*/page/1$')), get_all_pages),
        (pyoctopus.or_matcher(pyoctopus.url_matcher(r'.*/pages/.*\?query-3-page=\d+'),
                              pyoctopus.url_matcher(r'.*/search/.*/page/\d+')), pyoctopus.extractor(AlbumList)),
        (pyoctopus.url_matcher(r'.*/content/\d+/.*'), pyoctopus.extractor(AlbumDetails)),
        (pyoctopus.url_matcher(r'.*/content/\d+/.*'), resolve_img_urls),
        (pyoctopus.IMAGE, pyoctopus.downloader(os.path.expanduser('~/Downloads/4khd'), sub_dir_attr='name'))
    ]
    pyoctopus.new(store=store, sites=sites, processors=processors, threads=4).start(seed)
