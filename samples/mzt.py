import base64
import hashlib
import os.path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

import sample_logging
from pyoctopus import selector, converter, processor, matcher, site, limiter, new, Request, Response, store

sample_logging.setup()


@selector.hyperlink(
    selector.link(
        selector.xpath('//main//ul[contains(@class, "uk-grid")]//div[@class="uk-card-media-top"]//a/@href', multi=True),
        repeatable=False, priority=2),
    selector.link(selector.xpath('//a[@class="next page-numbers"]/@href', multi=False), repeatable=True, priority=1)
)
class AlbumList:
    pass


@selector.hyperlink(
    selector.link(selector.regex(r'.*/photo/(\d+)', group=1, selector=selector.xpath('//link[@rel="canonical"]/@href'),
                                 format_str='/app/post/p?id={}'), repeatable=False, priority=3,
                  attr_props=['id', 'name', 'url_prefix'])
)
class AlbumDetails:
    id = selector.regex(r'.*/photo/(\d+)', group=1, selector=selector.xpath('//link[@rel="canonical"]/@href'),
                        converter=converter.int_converter())
    name = selector.xpath('//h1[1]/text()', multi=False)
    url_prefix = selector.regex(r'^(.*)/[^/]+$', group=1, selector=selector.css('figure img', attr='src'))


def decode_mzt_image_response(res: Response) -> list[Request]:
    import json as _json
    j = _json.loads(res.text)
    _id = res.request.get_attr('id')
    a = ''
    for e in [x for x in range(18) if x >= 2]:
        a += str(_id % (e + 1) % 9)
    md5 = hashlib.md5()
    md5.update((str(_id) + 'Bxk80i9Rt').encode('utf-8'))
    b = md5.hexdigest()
    md5 = hashlib.md5()
    md5.update((a + b).encode('utf-8'))
    c = md5.hexdigest()[8:24]
    d = j['data'].split(b)[1]
    e = base64.b64decode(base64.b64encode(bytes.fromhex(d)))
    iv = a.encode('utf-8')
    cipher = AES.new(c.encode('utf-8'), AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(e)
    imgs = unpad(decrypted, AES.block_size).decode('utf-8')
    requests = []
    for img in _json.loads(imgs):
        requests.append(Request(res.request.get_attr('url_prefix') + '/' + img, priority=4, repeatable=False,
                                attrs={'id': _id, 'name': res.request.get_attr('name')}))
    return requests


if __name__ == '__main__':
    seed = 'https://kkmzt.com/photo/123107'
    proxy = 'http://127.0.0.1:7890'
    sites = [
        site('kkmzt.com', proxy=proxy, limiter=limiter(1, 0.75)),
        site('*.meizitu.*', proxy=proxy, limiter=limiter(1, 0.75))
    ]
    processors = [
        (matcher.url_matcher(r'.*/photo/page/.*'), processor.extractor(AlbumList)),
        (matcher.url_matcher(r'.*/photo/(\d+)'), processor.extractor(AlbumDetails)),
        (matcher.url_matcher(r'.*/app/post/p\?id=(\d+)'), decode_mzt_image_response),
        (matcher.IMAGE, processor.downloader(os.path.expanduser('~/Downloads/mzt'), sub_dir_attr='name'))
    ]
    octopus = new(processors=processors, sites=sites, threads=4,
                  # store=store.redis_store(prefix='mzt', password='123456'),
                  # store=store.sqlite_store(os.path.expanduser('~/Downloads/pyoctopus.db'), table='mzt')
                  )
    octopus.start(seed)
