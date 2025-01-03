import json
import logging
import sqlite3

from .store import Store
from ..reqeust import Request, State

_CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS {} (
		id TEXT PRIMARY KEY,
		url TEXT,
		method TEXT,
		priority INTEGER,
		repeatable INTEGER,
		parent TEXT,
		data BLOB,
		queries TEXT,
		headers TEXT,
		attrs TEXT,
		state TEXT,
        depth INTEGER,
        msg TEXT
)
'''


class SqliteStore(Store):
    def __init__(self, db: str, table: str = 'pyoctopus'):
        super(SqliteStore, self).__init__()
        self._db = db
        self._table = table
        self._init_table()

    def put(self, r: Request) -> bool:
        with sqlite3.connect(self._db) as _connection:
            try:
                _cursor = _connection.cursor()
                if self._exists(r.id):
                    _cursor.execute(
                        f'UPDATE {self._table} SET url = ?, method = ?, priority = ?, repeatable = ?, parent = ?, data = ?, queries = ?, headers = ?, attrs = ?, state = ?, depth = ?, msg = ? WHERE id = ?',
                        (r.url, r.method, r.priority, r.repeatable, r.parent, r.data, json.dumps(r.queries, ensure_ascii=False),
                         json.dumps(r.headers, ensure_ascii=False), json.dumps(r.attrs, ensure_ascii=False), State.WAITING.value, r.depth, r.msg, r.id,))
                    _connection.commit()
                else:
                    _cursor.execute(
                        f'INSERT INTO {self._table} (id, url, method, priority, repeatable, parent, data, queries, headers, attrs, state, depth, msg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (r.id, r.url, r.method, r.priority, r.repeatable, r.parent, r.data, json.dumps(r.queries, ensure_ascii=False),
                         json.dumps(r.headers, ensure_ascii=False),
                         json.dumps(r.attrs, ensure_ascii=False),
                         r.state.value, r.depth, r.msg))
                    _connection.commit()
                return True
            except sqlite3.Error as e:
                logging.exception("Put %s to sqlite failed", r)
                _connection.rollback()

    def get(self) -> Request | None:
        with sqlite3.connect(self._db) as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(
                    f'SELECT id, url, method, priority, repeatable, parent, data, queries, headers, attrs, state, depth, msg FROM {self._table} WHERE state = ? ORDER BY priority DESC LIMIT 1',
                    (State.WAITING.value,))
                row = _cursor.fetchone()
                if row is not None:
                    r = Request(row[1], method=row[2], priority=row[3],
                                repeatable=row[4],
                                data=row[6],
                                queries=json.loads(row[7]),
                                headers=json.loads(row[8]),
                                attrs=json.loads(row[9]))
                    r.id = row[0]
                    r.parent = row[5]
                    r.state = State(row[10])
                    r.depth = row[11]
                    r.msg = row[12]
                    _cursor.execute(
                        f'UPDATE {self._table} SET state = ?, msg = ? WHERE id = ?', (State.EXECUTING.value, '正在处理', r.id,))
                    _connection.commit()
                    return r
                return None
            except sqlite3.Error:
                logging.exception("Get request from sqlite failed")
                _connection.rollback()
                return None

    def update_state(self, r: Request, state: State, msg: str = None):
        r.state = state
        r.msg = msg
        with sqlite3.connect(self._db) as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(
                    f'UPDATE {self._table} SET state = ?, msg = ? WHERE id = ?', (state.value, msg, r.id,))
                _connection.commit()
            except sqlite3.Error:
                logging.exception(f"Update [{r}] state failed")
                _connection.rollback()

    def _exists(self, id: str) -> bool:
        with sqlite3.connect(self._db) as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(
                    f'SELECT count(1) FROM {self._table} WHERE id = ?', (id,))
                row = _cursor.fetchone()
                return row[0] > 0
            except sqlite3.Error:
                logging.exception("Create table failed")

    def _init_table(self):
        with sqlite3.connect(self._db) as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(_CREATE_TABLE_SQL.format(self._table))
                _cursor.execute(
                    f'CREATE INDEX IF NOT EXISTS idx_{self._table}_priority on {self._table}(priority)')
                _cursor.execute(f"UPDATE {self._table} set state = ?, msg = ? where state = ?",
                                (State.WAITING.value, '等待处理', State.EXECUTING.value))
                _connection.commit()
            except sqlite3.Error:
                logging.exception("Init table failed")
                _connection.rollback()


def new(db: str, table: str = 'pyoctopus') -> SqliteStore:
    return SqliteStore(db, table)
