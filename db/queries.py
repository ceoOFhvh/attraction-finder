"""Загрузка именованных запросов из единственного SQL-файла."""
from contextlib import closing
from functools import lru_cache

from db.database import BASE_DIR, get_connection


@lru_cache(maxsize=1)
def load_queries():
    text = (BASE_DIR / "sql" / "queries.sql").read_text(encoding="utf-8")
    queries = {}
    for block in text.split("-- name: ")[1:]:
        name, sql = block.split("\n", 1)
        queries[name.strip()] = sql.strip()
    return queries


def fetch_all(name, parameters=(), database=None):
    """Параметры передаются отдельно от SQL, соединение всегда закрывается."""
    with closing(get_connection(database)) as conn:
        cursor = conn.execute(load_queries()[name], parameters)
        return cursor.fetchall()


def fetch_one(name, parameters=(), database=None):
    with closing(get_connection(database)) as conn:
        cursor = conn.execute(load_queries()[name], parameters)
        return cursor.fetchone()
