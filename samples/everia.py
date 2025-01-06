import logging
import os.path

import pyoctopus

logging.basicConfig(level=logging.DEBUG)


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath('//div[@id="blog-entries"]/article//h2/a/@href', multi=True),
                   repeatable=False, priority=2),
    pyoctopus.link(pyoctopus.xpath(
        '//a[@class="next page-numbers"]/@href', multi=False), repeatable=False, priority=3)
)
class AlbumList:
    pass


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath(
        '//figure[@class="wp-block-gallery has-nested-images columns-1 wp-block-gallery-3 is-layout-flex wp-block-gallery-is-layout-flex"]/figure/img/@src',
        multi=True), repeatable=False, priority=1,
        attr_props=['name'])
)
class AlbumDetails:
    name = pyoctopus.xpath('//h1/text()')


if __name__ == '__main__':
    seed = 'https://everia.club/category/chinese/page/1/'
    proxy = 'http://127.0.0.1:7890'
    sites = [
        pyoctopus.site('everia.club', proxy=proxy,
                       limiter=pyoctopus.limiter(1, 0.75)),
        pyoctopus.site('*.top',
                       proxy=proxy,
                       limiter=pyoctopus.limiter(1, 0.75))
    ]
    processors = [
        (pyoctopus.url_matcher(r'.*/category/.*/page/(\d+)'),
         pyoctopus.extractor(AlbumList)),
        (pyoctopus.not_matcher(
            pyoctopus.or_matcher(pyoctopus.url_matcher(r'.*/category/.*/page/(\d+)'), pyoctopus.IMAGE)),
         pyoctopus.extractor(AlbumDetails)),
        (pyoctopus.IMAGE, pyoctopus.downloader(
            os.path.expanduser('~/Downloads/everia'), sub_dir_attr='name'))
    ]
    pyoctopus.new(processors=processors, sites=sites, threads=8, store=pyoctopus.sqlite_store(
        os.path.expanduser('~/Downloads/pyoctopus.db'), table='everia')).start(seed)
