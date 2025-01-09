import os

import pyoctopus
import sample_logging

sample_logging.setup()


class ProjectDetails:
    name = pyoctopus.css('.project-title a.title', text=True)

    address = pyoctopus.css('.project-title a.title', attr='href', multi=False, format_str='https://gitee.com{}')

    description = pyoctopus.css('.project-desc', text=True)

    tags = pyoctopus.css('.project-label-item', text=True, multi=True)

    stars = pyoctopus.css('.stars-count', text=True)


@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.xpath("//a[@rel='next'][position()=2]/@href"),
                   repeatable=False,
                   priority=1,
                   terminable=lambda x, _, __: x.page == 2))
class ProjectList:
    projects = pyoctopus.embedded(pyoctopus.css('.items .item', multi=True), ProjectDetails)
    page = pyoctopus.query('page', converter=pyoctopus.int_converter())


def collect(res):
    if res and res.projects:
        for project in res.projects:
            excel_collector(project)


excel_collector = pyoctopus.excel_collector(os.path.expanduser('~/Downloads/gitee.xlsx'), False, columns=[
    pyoctopus.excel_column('name', '名称'),
    pyoctopus.excel_column('address', '地址'),
    pyoctopus.excel_column('tags', '标签', style=pyoctopus.excel_style(delimiter='、')),
    pyoctopus.excel_column('stars', '星数'),
    pyoctopus.excel_column('description', '简介')
])

if __name__ == '__main__':
    seed = 'https://gitee.com/explore/all?order=starred'
    sites = [
        pyoctopus.site('gitee.com', limiter=pyoctopus.limiter(1))
    ]
    processors = [
        (pyoctopus.url_matcher(r'.*/explore/all\?order=starred.*'), pyoctopus.extractor(ProjectList, collector=collect))
    ]
    octopus = pyoctopus.new(processors=processors, sites=sites, threads=4)
    octopus.start(seed)
