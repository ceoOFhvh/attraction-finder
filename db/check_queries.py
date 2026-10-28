"""Проверка всех запросов: python -m db.check_queries [--cli]."""
import argparse
import sqlite3
import subprocess
import sys

from db.database import DEFAULT_DATABASE
from db.queries import fetch_all, load_queries

SAMPLES = {
    "catalog_name": (12, 12),
    "catalog_price": (12, 12),
    "category_list": (),
    "detail": (12, 12, 1),
    "free_places": (12, 12),
    "search": (12, 12, "", "", None, None, 500, 500, 12, 12, 12),
    "category_detail": ("музей",),
    "category_places": (12, 12, 1),
    "overview": (),
    "free_count": (),
    "category_stats": (),
    "price_groups": (),
    "popular_categories": (1,),
    "home_preview": (12, 12, 3, 0),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", action="store_true",
                        help="Дополнительно выполнить в CLI Python 3.12+")
    args = parser.parse_args()
    if args.cli and sys.version_info < (3, 12):
        parser.error("Встроенный CLI sqlite3 требует Python 3.12 или новее")
    for name, sql in load_queries().items():
        params = SAMPLES[name]
        rows = fetch_all(name, params)
        print(name, "— строк:", len(rows))
        for row in rows:
            print(dict(row))
        if args.cli:
            # CLI не принимает tuple параметров. Только для фиксированных
            # учебных примеров используем литералы, экранированные SQLite.
            # Веб-приложение всегда использует execute(sql, parameters).
            conn = sqlite3.connect(":memory:")
            try:
                literals = [conn.execute("SELECT quote(?)", (value,))
                            .fetchone()[0] for value in params]
            finally:
                conn.close()
            parts = sql.split("?")
            assert len(parts) == len(literals) + 1
            command = parts[0] + "".join(
                value + tail for value, tail in zip(literals, parts[1:])
            )
            result = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "sqlite3",
                 str(DEFAULT_DATABASE), command],
                capture_output=True, text=True, encoding="utf-8",
            )
            if result.returncode or "Error:" in result.stderr:
                raise RuntimeError(result.stderr)
            print("CLI: OK")
    print("Проверены все", len(SAMPLES), "запросов.")


if __name__ == "__main__":
    main()
