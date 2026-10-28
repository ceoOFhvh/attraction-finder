"""python -m db.import_json: создание схемы и повторяемый импорт JSON."""
import argparse
import json
import math
from pathlib import Path

from db.database import BASE_DIR, DEFAULT_DATABASE, get_connection


def validate_records(records):
    """Проверить исходные записи до изменения данных в базе."""
    if not isinstance(records, list):
        raise ValueError("JSON должен содержать список объектов")
    seen = set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Каждая запись должна быть объектом JSON")
        ident = item.get("id")
        if type(ident) is not int or ident <= 0 or ident in seen:
            raise ValueError("id должен быть уникальным положительным числом")
        seen.add(ident)
        for key in ("name", "category"):
            if not isinstance(item.get(key), str):
                raise ValueError("Название и категория должны быть строками")
        if not item["name"].strip():
            raise ValueError("Название не может быть пустым")
        start, end = item.get("open_hour"), item.get("close_hour")
        if (type(start) is not int or type(end) is not int
                or not 0 <= start < end <= 24):
            raise ValueError("Ожидается дневной интервал от 0 до 24 часов")
        price = item.get("price")
        if (type(price) not in (int, float) or not math.isfinite(price)
                or price < 0):
            raise ValueError("Цена: конечное число не меньше нуля")
        if item.get("description") is not None:
            if not isinstance(item["description"], str):
                raise ValueError("Описание: строка либо null")


def import_data(source=None, database=None):
    source = Path(source or BASE_DIR / "data" / "attractions.json")
    records = json.loads(source.read_text(encoding="utf-8-sig"))
    validate_records(records)
    conn = get_connection(database or DEFAULT_DATABASE, create=True)
    try:
        schema = (BASE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8")
        conn.executescript(schema)
        categories = {}
        for item in records:
            name = item["category"].strip() or "Без категории"
            categories.setdefault(name.casefold(), name)
        conn.executemany(
            "INSERT INTO categories (name_key, name) VALUES (?, ?) "
            "ON CONFLICT(name_key) DO NOTHING",
            list(categories.items()),
        )
        category_ids = {
            row["name_key"]: row["id"]
            for row in conn.execute("SELECT id, name_key FROM categories")
        }
        values = []
        for item in records:
            key = (item["category"].strip() or "Без категории").casefold()
            values.append((
                item["id"], item["name"], item["name"].casefold(),
                category_ids[key], item["open_hour"], item["close_hour"],
                item["price"], item.get("description"),
            ))
        conn.executemany(
            """INSERT INTO attractions
               (id, name, search_name, category_id, open_hour, close_hour,
                price, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, search_name=excluded.search_name,
                 category_id=excluded.category_id,
                 open_hour=excluded.open_hour, close_hour=excluded.close_hour,
                 price=excluded.price, description=excluded.description""",
            values,
        )
        conn.commit()
        return len(records)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        count = import_data(args.source, args.database)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + "\n")
    print("Импортировано записей:", count)
    print("База:", args.database.resolve())


if __name__ == "__main__":
    main()
