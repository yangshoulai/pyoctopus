import logging
import os.path

import pyoctopus
import sample_logging

sample_logging.setup()
_logger = logging.getLogger('pyoctopus.sample.everia')

_ALBUMS_PAGE_REPEATABLE = False


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath('//div[@id="blog-entries"]/article//h2/a/@href', multi=True),
                   repeatable=False, priority=2, attr_props=['category']),
    pyoctopus.link(pyoctopus.xpath(
        '//a[@class="next page-numbers"]/@href', multi=False), repeatable=_ALBUMS_PAGE_REPEATABLE, priority=3)
)
class AlbumList:
    category = pyoctopus.regex(r'.*/category/(.*)/page/.*', group=1, selector=pyoctopus.url())


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath(
        '//figure[@class="wp-block-gallery has-nested-images columns-1 wp-block-gallery-3 is-layout-flex wp-block-gallery-is-layout-flex"]/figure/img/@src',
        multi=True),
        repeatable=False,
        priority=1,
        inherit=True,
        attr_props=['name', 'dir', 'category']),
    pyoctopus.link(pyoctopus.xpath('//div[@id="content"]/article//div[@class="separator"]//img/@src', multi=True),
                   repeatable=False,
                   priority=1,
                   inherit=True,
                   attr_props=['name', 'dir', 'category'])
)
class AlbumDetails:
    name = pyoctopus.xpath('//h1/text()')
    dir = pyoctopus.regex(r'.*/(\d{4})/(\d{2})/(\d{2})/.*', group=[1, 2, 3], selector=pyoctopus.url(url_decode=True))


if __name__ == '__main__':
    _logger.debug('Starting everia.club crawler')
    seed = 'https://everia.club/category/chinese/page/1/'
    proxy = 'http://127.0.0.1:7890'
    sites = [
        pyoctopus.site('everia.club', proxy=proxy,
                       limiter=pyoctopus.limiter(1, 1)),
        pyoctopus.site('*',
                       proxy=proxy,
                       limiter=pyoctopus.limiter(1, 1))
    ]
    processors = [
        (pyoctopus.url_matcher(r'.*/category/.*/page/(\d+)'), pyoctopus.extractor(AlbumList)),
        (pyoctopus.url_matcher(r'.*/\d{4}/\d{2}/\d{2}/.*'), pyoctopus.extractor(AlbumDetails)),
        (pyoctopus.IMAGE,
         pyoctopus.downloader(os.path.expanduser('~/Downloads/everia'), sub_dir_attr=['category', 'dir', 'name']))
    ]
    (pyoctopus.new(processors=processors,
                   sites=sites,
                   store=pyoctopus.sqlite_store(os.path.expanduser('~/Downloads/pyoctopus.db'), table='everia'))
     .start(pyoctopus.request(seed, repeatable=_ALBUMS_PAGE_REPEATABLE)))
