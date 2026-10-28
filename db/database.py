"""Подключение SQLite напрямую, без Django ORM."""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = BASE_DIR / "data" / "attractions.sqlite"


def get_connection(path=None, *, create=False):
    """Row даёт доступ по именам; каждое подключение проверяет FK."""
    if path is None:
        try:
            from django.conf import settings
        except ImportError:
            path = DEFAULT_DATABASE
        else:
            path = (settings.SQLITE_PATH if settings.configured
                    else DEFAULT_DATABASE)
    path = Path(path).resolve()
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
    else:
        # Веб-запрос не должен незаметно создать пустую базу по неверному пути.
        conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
