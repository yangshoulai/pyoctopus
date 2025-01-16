import os
import sample_logging
import pyoctopus
from dataclasses import dataclass
from typing import List, Optional
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager

sample_logging.setup()

WALLHAVEN_API_KEY = "px7O1PPw8hk5YepgLgzc2qABgR1Astnf"

WALLHAVEN_API_QUERIES = {
    "apikey": WALLHAVEN_API_KEY,
    "q": "",
    "purity": "111",
    "atleast": "1920x1080",
    "page": "1",
}


class WallpaperDetailsResponse:
    id = pyoctopus.json("$.data.id")
    url = pyoctopus.json("$.data.url")
    short_url = pyoctopus.json("$.data.short_url")
    ratio = pyoctopus.json("$.data.ratio", converter=pyoctopus.float_converter())
    category = pyoctopus.json("$.data.category")
    purity = pyoctopus.json("$.data.purity")
    width = pyoctopus.json("$.data.dimension_x", converter=pyoctopus.int_converter())
    height = pyoctopus.json("$.data.dimension_y", converter=pyoctopus.int_converter())
    file_size = pyoctopus.json("$.data.file_size", converter=pyoctopus.int_converter())
    file_type = pyoctopus.json("$.data.file_type")
    created_at = pyoctopus.json("$.data.created_at")
    src = pyoctopus.json("$.data.path")
    colors = pyoctopus.json("$.data.colors[*]", multi=True)
    tags = pyoctopus.json("$.data.tags[*].name", multi=True)
    uploader = pyoctopus.json("$.data.uploader.username")

    large_url = pyoctopus.json("$.data.thumbs.large")
    original_url = pyoctopus.json("$.data.thumbs.original")
    small_url = pyoctopus.json("$.data.thumbs.small")


@pyoctopus.hyperlink(
    pyoctopus.link(
        pyoctopus.json(
            "$.data[*].id", multi=True, format_str="https://wallhaven.cc/api/v1/w/{}?apikey=" + WALLHAVEN_API_KEY
        ),
        repeatable=False,
        priority=0,
    ),
)
class WallpaperSearchResponse:
    current_page = pyoctopus.json("$.meta.current_page", converter=pyoctopus.int_converter(1))
    last_page = pyoctopus.json("$.meta.last_page", converter=pyoctopus.int_converter(1))
    total = pyoctopus.json("$.meta.total", converter=pyoctopus.int_converter(1))


def _process_search_response(resp: pyoctopus.Response):
    requests = []

    def _collect(w: WallpaperSearchResponse):
        if w.last_page > w.current_page:
            requests.append(
                pyoctopus.request(
                    f"https://wallhaven.cc/api/v1/search", priority=1,
                    queries={**WALLHAVEN_API_QUERIES, "page": w.current_page + 1}
                )
            )

    wallpapers = pyoctopus.extractor(WallpaperSearchResponse, _collect)(resp)
    requests.extend(wallpapers)
    return requests


class WallhavenDB:
    """Wallhaven 数据库操作类"""

    def __init__(self, db_path: str):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表结构和索引"""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # 创建壁纸信息表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS wallpapers (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    short_url TEXT,
                    ratio REAL,
                    category TEXT,
                    purity TEXT,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    file_type TEXT,
                    created_at TEXT,
                    src TEXT,
                    colors TEXT,
                    tags TEXT,
                    uploader TEXT,
                    thumbs TEXT
                )
            """
            )

            # 创建索引
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_wallhaven_category 
                ON wallpapers(category)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_wallhaven_purity 
                ON wallpapers(purity)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_wallhaven_created_at 
                ON wallpapers(created_at)
            """
            )

            conn.commit()

    def save_wallpaper(self, wallpaper: WallpaperDetailsResponse) -> bool:
        """保存壁纸信息

        Args:
            wallpaper: 壁纸详细信息对象

        Returns:
            bool: 保存是否成功
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                wallpaper_data = {
                    "id": wallpaper.id,
                    "url": wallpaper.url,
                    "short_url": wallpaper.short_url,
                    "ratio": wallpaper.ratio,
                    "category": wallpaper.category,
                    "purity": wallpaper.purity,
                    "width": wallpaper.width,
                    "height": wallpaper.height,
                    "file_size": wallpaper.file_size,
                    "file_type": wallpaper.file_type,
                    "created_at": wallpaper.created_at,
                    "src": wallpaper.src,
                    "colors": json.dumps(wallpaper.colors) if wallpaper.colors else "[]",
                    "tags": json.dumps(wallpaper.tags) if wallpaper.tags else "[]",
                    "uploader": wallpaper.uploader,
                    "thumbs": json.dumps(
                        {"large": wallpaper.large_url, "original": wallpaper.original_url, "small": wallpaper.small_url}
                    ),
                }

                # 使用 UPSERT 语法，如果记录存在则更新
                cursor.execute(
                    """
                    INSERT INTO wallpapers (
                        id, url, short_url, ratio, category, purity, 
                        width, height, file_size, file_type, created_at,
                        src, colors, tags, uploader, thumbs
                    ) VALUES (
                        :id, :url, :short_url, :ratio, :category, :purity,
                        :width, :height, :file_size, :file_type, :created_at,
                        :src, :colors, :tags, :uploader, :thumbs
                    ) ON CONFLICT(id) DO UPDATE SET
                        url=:url, short_url=:short_url, ratio=:ratio,
                        category=:category, purity=:purity, width=:width,
                        height=:height, file_size=:file_size, file_type=:file_type,
                        created_at=:created_at, src=:src, colors=:colors,
                        tags=:tags, uploader=:uploader, thumbs=:thumbs
                """,
                    wallpaper_data,
                )

                conn.commit()
                return True

        except Exception as e:
            print(f"保存壁纸信息时发生错误: {str(e)}")
            return False


# 创建数据库实例
db = WallhavenDB(os.path.expanduser("~/Downloads/wallhaven.db"))


def _collect_wallpaper_details(w: WallpaperDetailsResponse):
    """收集壁纸详细信息并保存到数据库"""
    if w:
        db.save_wallpaper(w)


if __name__ == "__main__":
    seed = pyoctopus.request(
        "https://wallhaven.cc/api/v1/search", queries={**WALLHAVEN_API_QUERIES, "page": ["1"]}, priority=1
    )
    proxy = "http://127.0.0.1:7890"
    store = pyoctopus.sqlite_store(os.path.expanduser("~/Downloads/wallhaven.db"), table="wallhaven")
    sites = [
        pyoctopus.site("wallhaven.cc", proxy=proxy, limiter=pyoctopus.limiter(2)),
    ]

    processors = [
        (pyoctopus.url_matcher(r".*/api/v1/search"), _process_search_response),
        (
            pyoctopus.url_matcher(r".*/w/.*"),
            pyoctopus.extractor(WallpaperDetailsResponse, collector=_collect_wallpaper_details),
        ),
    ]

    octopus = pyoctopus.new(processors=processors, sites=sites, store=store, threads=2)
    octopus.start(seed)
