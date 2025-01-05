import logging
import os.path

from ..pyoctopus import * 

logging.basicConfig(level=logging.INFO)


@hyperlink(
    link(xpath('//div[@id="blog-entries"]/article/h2/a/@href', multi=True),
                   repeatable=False, priority=1),
    link(xpath(
        '//a[@class="next page-numbers"]/@href', multi=False), repeatable=False, priority=2)
)
class AlbumList:
    pass


@hyperlink(
    link(xpath('//figure[@class="wp-block-gallery has-nested-images columns-1 wp-block-gallery-3 is-layout-flex wp-block-gallery-is-layout-flex"]/figure/img/@src', multi=True), repeatable=False, priority=3,
                   attr_props=['name'])
)
class AlbumDetails:
    name = xpath('//h1/text()')


if __name__ == '__main__':
    seed = 'https://everia.club/category/chinese/page/1/'
    proxy = 'http://127.0.0.1:7890'
    sites = [
        site('everia.club', proxy=proxy,
                       limiter=limiter(1, 0.5)),
        site('takobox.top', 
                       # proxy=proxy,
                       limiter=limiter(1, 0.5))
    ]
    processors = [
        (url_matcher(r'.*/\?page=(\d+)'), extractor(AlbumList)),
        (url_matcher(r'.*/photo.php\?id=.*'),
         extractor(AlbumDetails)),
        (IMAGE, downloader(
            os.path.expanduser('~/Downloads/everia'), sub_dir_attr='name'))
    ]
    new(processors=processors, sites=sites, threads=2, store=sqlite_store(
        os.path.expanduser('~/Downloads/db'), table='everia')).start(seed)
