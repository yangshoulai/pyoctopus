import json
import sqlite3
import threading

from .store import Store
from ..request import Request, State

_COL_ID = ("id", "TEXT PRIMARY KEY")
_COLS = [
    ("url", "TEXT"),
    ("method", "TEXT"),
    ("priority", "INTEGER"),
    ("repeatable", "INTEGER"),
    ("parent", "TEXT"),
    ("data", "BLOB"),
    ("queries", "TEXT"),
    ("headers", "TEXT"),
    ("attrs", "TEXT"),
    ("state", "TEXT"),
    ("depth", "INTEGER"),
    ("msg", "TEXT"),
    ("inherit", "INTEGER"),
]

_SQL_CREATE_TABLE = "CREATE TABLE IF NOT EXISTS {} (" + ", ".join([f"{c[0]} {c[1]}" for c in [_COL_ID, *_COLS]]) + ")"

_COL_NAMES = ", ".join([c[0] for c in [_COL_ID, *_COLS]])

_COL_UPDATE_BY_ID = ", ".join([f"{c[0]} = ?" for c in [*_COLS]])

_local = threading.local()


class SqliteStore(Store):
    def __init__(self, db: str, table: str = "pyoctopus"):
        super(SqliteStore, self).__init__()
        self._db = db
        self._table = table

        self._sql_create_table = _SQL_CREATE_TABLE.format(self._table)
        self._sql_create_idx_priority = (
            f"CREATE INDEX IF NOT EXISTS idx_{self._table}_priority on {self._table}(priority)"
        )
        self._sql_exist_by_id = f"SELECT count(1) FROM {self._table} WHERE id = ?"
        self._sql_update_state_by_id = f"UPDATE {self._table} SET state = ?, msg = ? WHERE id = ?"
        self._sql_get = f"SELECT {_COL_NAMES} FROM {self._table} WHERE state = ? ORDER BY priority DESC LIMIT 1"
        self._sql_update_by_id = f"UPDATE {self._table} SET {_COL_UPDATE_BY_ID} WHERE id = ?"
        self._sql_put = (
            f'INSERT INTO {self._table} ({_COL_NAMES}) VALUES ({", ".join(["?" for _ in [_COL_ID, *_COLS]])})'
        )
        self._sql_update_state = f"UPDATE {self._table} SET state = ?, msg = ? WHERE state = ?"
        self._sql_paged_select = f"SELECT {_COL_NAMES} FROM {self._table} WHERE state = ? LIMIT ? OFFSET ?"
        self._sql_count_by_state = f"SELECT count(1) FROM {self._table} WHERE state = ?"
        self._init_table()

    def put(self, r: Request) -> bool:
        with self._get_connection() as _connection:
            try:
                _cursor = _connection.cursor()
                if self.exists(r.id):
                    _cursor.execute(
                        self._sql_update_by_id,
                        (
                            r.url,
                            r.method,
                            r.priority,
                            r.repeatable,
                            r.parent,
                            r.data,
                            json.dumps(r.queries, ensure_ascii=False),
                            json.dumps(r.headers, ensure_ascii=False),
                            json.dumps(r.attrs, ensure_ascii=False),
                            State.WAITING.value,
                            r.depth,
                            r.msg,
                            r.inherit,
                            r.id,
                        ),
                    )
                else:
                    _cursor.execute(
                        self._sql_put,
                        (
                            r.id,
                            r.url,
                            r.method,
                            r.priority,
                            r.repeatable,
                            r.parent,
                            r.data,
                            json.dumps(r.queries, ensure_ascii=False),
                            json.dumps(r.headers, ensure_ascii=False),
                            json.dumps(r.attrs, ensure_ascii=False),
                            r.state.value,
                            r.depth,
                            r.msg,
                            r.inherit,
                        ),
                    )
                _connection.commit()
                return True
            except sqlite3.Error as e:
                _connection.rollback()
                raise e

    def _row_to_request(self, row) -> Request:
        r = Request(
            row[1],
            method=row[2],
            priority=row[3],
            repeatable=row[4],
            data=row[6],
            queries=json.loads(row[7]),
            headers=json.loads(row[8]),
            attrs=json.loads(row[9]),
        )
        r.id = row[0]
        r.parent = row[5]
        r.state = State(row[10])
        r.depth = row[11]
        r.msg = row[12]
        r.inherit = bool(row[13])
        return r

    def get(self) -> Request | None:
        with self._get_connection() as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(self._sql_get, (State.WAITING.value,))
                row = _cursor.fetchone()
                if row is not None:
                    r = self._row_to_request(row)
                    r.state = State.EXECUTING
                    r.msg = "正在处理"
                    _cursor.execute(
                        self._sql_update_state_by_id,
                        (
                            State.EXECUTING.value,
                            "正在处理",
                            r.id,
                        ),
                    )
                    return r
                _connection.commit()
                return None
            except sqlite3.Error as e:
                _connection.rollback()
                raise e

    def update_state(self, r: Request, state: State, msg: str = None):
        r.state = state
        r.msg = msg
        with self._get_connection() as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(
                    self._sql_update_state_by_id,
                    (
                        state.value,
                        msg,
                        r.id,
                    ),
                )
                _connection.commit()
            except sqlite3.Error as e:
                _connection.rollback()
                raise e

    def exists(self, id: str) -> bool:
        with self._get_connection() as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(self._sql_exist_by_id, (id,))
                row = _cursor.fetchone()
                _connection.commit()
                return row[0] > 0
            except sqlite3.Error as e:
                raise e

    def _init_table(self):
        with sqlite3.connect(self._db) as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(self._sql_create_table.format(self._table))
                _cursor.execute(self._sql_create_idx_priority)
                _cursor.execute(self._sql_update_state, (State.WAITING.value, "等待处理", State.EXECUTING.value))
                _connection.commit()
            except sqlite3.Error as e:
                _connection.rollback()
                raise e

    def reply_failed(self) -> int:
        with self._get_connection() as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(self._sql_update_state, (State.WAITING.value, "等待处理", State.FAILED.value))
                _connection.commit()
                return _cursor.rowcount
            except sqlite3.Error as e:
                _connection.rollback()
                raise e

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(_local, "conn"):
            _local.conn = sqlite3.connect(self._db)
        return _local.conn

    def get_statistics(self) -> tuple[int, int, int, int, int]:
        with self._get_connection() as _connection:
            try:
                _cursor = _connection.cursor()
                _cursor.execute(f"select count(1) from {self._table}")
                all = _cursor.fetchone()[0]
                _cursor.execute(self._sql_count_by_state, (State.WAITING.value,))
                waiting = _cursor.fetchone()[0]
                _cursor.execute(self._sql_count_by_state, (State.EXECUTING.value,))
                executing = _cursor.fetchone()[0]
                _cursor.execute(self._sql_count_by_state, (State.COMPLETED.value,))
                completed = _cursor.fetchone()[0]
                _cursor.execute(self._sql_count_by_state, (State.FAILED.value,))
                failed = _cursor.fetchone()[0]
                _connection.commit()
                return all, waiting, executing, completed, failed
            except sqlite3.Error as e:
                _connection.rollback()
                raise e

    def has_waiting_requests(self) -> bool:
        with self._get_connection() as _connection:
            _cursor = _connection.cursor()
            _cursor.execute(self._sql_count_by_state, (State.WAITING.value,))
            if _cursor.fetchone()[0] <= 0:
                _cursor.execute(self._sql_count_by_state, (State.EXECUTING.value,))
                return _cursor.fetchone()[0] > 0
            return True


def new(db: str, table: str = "pyoctopus") -> SqliteStore:
    return SqliteStore(db, table)
