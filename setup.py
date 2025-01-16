from setuptools import setup, find_packages

setup(
    name='pyoctopus',                    # 库的名称
    version='0.1.0',                     # 库的版本
    packages=find_packages(),            # 自动查找并包含所有模块
    install_requires=[                   # 项目的依赖包
        'requests',                      # 示例依赖
        'beautifulsoup4',
        'jsonpath_ng',
        'lxml',
        'tornado'
    ],
    author='yangshoulai',                  # 作者信息
    author_email='shoulai.yang@gmail.com',  # 作者邮箱
    description='A simple Python library for web crawler',  # 库的简短描述
    long_description=open('README.md').read(),  # 从 README.md 中读取库的详细描述
    long_description_content_type='text/markdown',
    url='https://github.com/yangsholai/pyoctopus',  # 项目的 GitHub 地址
    classifiers=[                        # 分类信息
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',             # 适用的 Python 版本
)
