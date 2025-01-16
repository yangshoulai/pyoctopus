# PyOctopus

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

PyOctopus 是一个强大的多线程爬虫框架，提供了丰富的内容提取方式和灵活的数据处理机制。

## 核心特性

- **多线程抓取**: 支持多线程并发抓取，内置限速控制
- **多种解析器**: 支持 XPath、CSS、JsonPath、正则表达式等多种解析方式
- **数据存储**: 支持 SQLite、Redis 等多种存储方式
- **灵活扩展**: 支持自定义处理器和收集器
- **智能调度**: 支持请求优先级和可重复性控制

## 快速开始

### 安装

```bash
pip install pyoctopus
```

### 基础示例

```python
import pyoctopus

# 定义数据模型
@pyoctopus.hyperlink(
    pyoctopus.link(pyoctopus.css('.item a', multi=True, attr='href'),
                   repeatable=False, priority=1)
)
class ProjectDetails:
    name = pyoctopus.css('.project-title', text=True)
    description = pyoctopus.css('.project-desc', text=True)
    tags = pyoctopus.css('.tag', text=True, multi=True)

# 配置爬虫
sites = [
    pyoctopus.site('example.com', limiter=pyoctopus.limiter(1))
]

processors = [
    (pyoctopus.url_matcher(r'.*'), pyoctopus.extractor(ProjectDetails))
]

# 启动爬虫
octopus = pyoctopus.new(processors=processors, sites=sites, threads=4)
octopus.start('https://example.com')
```

## 高级特性

### 1. 多种解析方式

```python
class DataModel:
    # XPath 提取
    title = pyoctopus.xpath('//h1/text()')

    # CSS 选择器
    description = pyoctopus.css('.content p', text=True)

    # JsonPath 提取
    data = pyoctopus.jsonpath('$.data.items[*]')

    # 正则表达式
    id = pyoctopus.regex(r'ID:(\d+)', group=1)
```

### 2. 数据存储

```python
# SQLite 存储
store = pyoctopus.sqlite_store('data.db', table='spider_data')

# Redis 存储
store = pyoctopus.redis_store(prefix='spider', password='123456')
```

### 3. 自定义收集器

```python
# Excel 收集器
excel_collector = pyoctopus.excel_collector('output.xlsx', columns=[
    pyoctopus.excel_column('name', '名称'),
    pyoctopus.excel_column('description', '描述'),
    pyoctopus.excel_column('tags', '标签',
                          style=pyoctopus.excel_style(delimiter='、'))
])

# 日志收集器
logging_collector = pyoctopus.logging_collector()
```

### 4. 请求控制

```python
# 站点配置
sites = [
    pyoctopus.site('example.com',
                   proxy='http://127.0.0.1:7890',        # 代理设置
                   limiter=pyoctopus.limiter(0.5))       # 限速配置
]

# 请求属性
request = pyoctopus.request(
    url='https://example.com',
    priority=1,                # 优先级
    repeatable=False,         # 是否可重复
    attrs={'category': 'news'} # 自定义属性
)
```

## 项目结构

```
pyoctopus/
├── core/           # 核心实现
├── processor/      # 处理器
├── selector/       # 选择器
├── store/          # 存储实现
└── utils/          # 工具函数
```

## 最佳实践

1. 合理使用限速控制，避免对目标站点造成压力
2. 选择合适的解析方式，提高解析效率
3. 使用优先级控制抓取顺序
4. 做好异常处理和日志记录
5. 合理设置线程数量

## 开发指南

### 打包项目

1. 安装打包工具

```bash
pip install build twine
```

2. 构建项目

```bash
python3 setup.py sdist bdist_wheel
```

这将在 `dist/` 目录下生成源码包（.tar.gz）和轮子包（.whl）。

3. 清理构建文件

```bash
# 清理构建文件
python3 setup.py clean --all   # 清理 build 目录
rm -rf dist/                   # 删除 dist 目录
rm -rf *.egg-info/            # 删除 egg-info 目录
```

### 发布到 PyPI

1. 注册 PyPI 账号
   访问 [PyPI](https://pypi.org/) 注册账号。

2. 创建 API Token
   在 PyPI 账号设置中创建 API Token，用于发布认证。

3. 配置认证信息
   创建或编辑 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = your-api-token
```

4. 上传到 PyPI

```bash
twine upload dist/*
```

5. 验证安装

```bash
pip install pyoctopus
```

## 贡献指南

欢迎提交 Pull Request 或 Issue。详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 开源协议

本项目采用 MIT 协议，详见 [LICENSE](LICENSE) 文件。
