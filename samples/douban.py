import logging
import os

import pyoctopus

logging.basicConfig(level=logging.INFO)
logging.info("")


class MovieActor:
    id = pyoctopus.regex("^.*/(\\d+)/$", 1, pyoctopus.xpath("//a/@href"), converter=pyoctopus.int_converter())
    name = pyoctopus.css('a', text=True)

    def __str__(self):
        return f"{self.name}({self.id})"


@pyoctopus.hyperlink(pyoctopus.link(pyoctopus.css('.item div.hd > a', multi=True, attr='href'), repeatable=False),
                     pyoctopus.link(pyoctopus.css('span.next a', attr='href'), repeatable=False))
class DoubanMovie:
    name = pyoctopus.xpath('//h1/span[1]/text()')
    score = pyoctopus.xpath('//strong[@class="ll rating_num"]/text()', converter=pyoctopus.float_converter())
    directors = pyoctopus.xpath('//a[@rel="v:directedBy"]/text()', multi=True)
    writers = pyoctopus.xpath("//span[text()='编剧']/../span[@class='attrs']/a/text()", multi=True)
    actors = pyoctopus.embedded(pyoctopus.xpath("//a[@rel='v:starring']", multi=True), MovieActor)
    types = pyoctopus.xpath("//span[@property='v:genre']/text()", multi=True)
    local = pyoctopus.xpath("//span[text()='制片国家/地区:']/following::text()")
    languages = pyoctopus.regex("语言:</span>([\\S\\s]*?)<br/>", multi=True, group=1)
    published_date = pyoctopus.regex(r'^([^(]*)', 1, pyoctopus.xpath("//span[@property='v:initialReleaseDate']/text()"))
    duration = pyoctopus.xpath("//span[@property='v:runtime']/@content", converter=pyoctopus.int_converter())
    imdb = pyoctopus.xpath("//span[text()='IMDb:']/following::text()")
    brief = pyoctopus.xpath("//div[@id='link-report-intra']//span[@property='v:summary']/text()")

    def __str__(self):
        return f"{{name={self.name}, score={self.score}, published_date={self.published_date}, imdb={self.imdb}}}"


excel_collector = pyoctopus.excel_collector(os.path.expanduser('~/Downloads/movies.xlsx'), False, columns=[
    pyoctopus.excel_column('name', '片名'),
    pyoctopus.excel_column('score', '得分'),
    pyoctopus.excel_column('published_date', '发布日期'),
    pyoctopus.excel_column('imdb', 'imdb'),
    pyoctopus.excel_column('directors', '导演', style=pyoctopus.excel_style(delimiter='、')),
    pyoctopus.excel_column('writers', '编剧', style=pyoctopus.excel_style(delimiter='、')),
    pyoctopus.excel_column('actors', '演员'),
    pyoctopus.excel_column('types', '类型'),
    pyoctopus.excel_column('local', '地区'),
    pyoctopus.excel_column('languages', '语言'),
    pyoctopus.excel_column('duration', '时长（分）'),
    pyoctopus.excel_column('brief', '简介')
])


def collect(movie):
    if movie.__dict__.get('name', None) is not None:
        excel_collector(movie)


if __name__ == '__main__':
    sites = [pyoctopus.site('*.douban.com', limiter=pyoctopus.limiter(1, 2),
                            headers={
                                'Cookie':
                                    'bid=yicCcYhs54g; _pk_id.100001.4cf6=01a72de6dae49fa9.1735540670.; ll="118159"; _vwo_uuid_v2=D419D8996E4C1053ECC587950BC59112A|a05f2eb1bab00d520f398d30ca0b282d; __utmc=30149280; __utmc=223695111; dbcl2="142644688:5lmuuXqB8lk"; ck=eW3a; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1735795936%2C%22https%3A%2F%2Fopen.weixin.qq.com%2F%22%5D; _pk_ses.100001.4cf6=1; __utma=30149280.1215891002.1724233909.1735787308.1735795937.6; __utmb=30149280.0.10.1735795937; __utmz=30149280.1735795937.6.3.utmcsr=open.weixin.qq.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=223695111.1198329190.1735540670.1735787308.1735795937.4; __utmb=223695111.0.10.1735795937; __utmz=223695111.1735795937.4.2.utmcsr=open.weixin.qq.com|utmccn=(referral)|utmcmd=referral|utmcct=/; push_noty_num=0; push_doumail_num=0'
                            }
                            )]
    octopus = pyoctopus.new(
        processors=[(pyoctopus.ALL, pyoctopus.extractor(DoubanMovie, collector=collect))],
        sites=sites
    )
    octopus.start('https://movie.douban.com/top250?start=0&filter')
