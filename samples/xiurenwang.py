import os.path

import pyoctopus
import sample_logging

sample_logging.setup()


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath('//div[@class="paragraph"]/div[@class="title"]/a/@href', multi=True),
                   repeatable=False, priority=1),
    pyoctopus.link(pyoctopus.xpath(
        '//a[@class="next"]/@href', multi=False), repeatable=False, priority=2)
)
class AlbumList:
    pass


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath('//div[@class="intro"]/img/@src', multi=True), repeatable=False, priority=3,
                   attr_props=['name'])
)
class AlbumDetails:
    id = pyoctopus.query('id')
    name = pyoctopus.xpath('//h1/text()')

    def __str__(self):
        return f'{self.id} {self.name}'


if __name__ == '__main__':
    seed = 'https://xiurenwang.me/?page=1'
    proxy = 'http://127.0.0.1:7890'
    sites = [
        pyoctopus.site('xiurenwang.me', proxy=proxy, limiter=pyoctopus.limiter(0.5)),
        pyoctopus.site('*.xchina.*', proxy=proxy, limiter=pyoctopus.limiter(0.5))
    ]
    processors = [
        (pyoctopus.url_matcher(r'.*/\?page=(\d+)'), pyoctopus.extractor(AlbumList)),
        (pyoctopus.url_matcher(r'.*/photo.php\?id=.*'),
         pyoctopus.extractor(AlbumDetails, collector=pyoctopus.logging_collector())),
        (pyoctopus.IMAGE, pyoctopus.downloader(os.path.expanduser('~/Downloads/xiurenwang'), sub_dir_attr='name'))
    ]
    pyoctopus.new(processors=processors, sites=sites, threads=2, store=pyoctopus.sqlite_store(
        os.path.expanduser('~/Downloads/pyoctopus.db'), table='xiuirenwang')).start(seed)
