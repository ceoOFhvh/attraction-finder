"""Проверка импорта, ограничений и запросов на отдельной временной базе."""
import json
import sqlite3
from contextlib import closing

import pytest

from db.database import get_connection
from db.import_json import import_data
from db.queries import fetch_all, fetch_one, load_queries


@pytest.fixture
def source(tmp_path):
    records = [
        {"id": 5, "name": "Музей", "category": "музей",
         "open_hour": 10, "close_hour": 18, "price": 200},
        {"id": 9, "name": "Галерея", "category": "музей",
         "open_hour": 9, "close_hour": 20, "price": 100,
         "description": "Картины"},
        {"id": 12, "name": "Парк", "category": "парк",
         "open_hour": 6, "close_hour": 23, "price": 0},
    ]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def test_import_preserves_ids_relations_and_source(source, tmp_path):
    database = tmp_path / "test.sqlite"
    before = source.read_bytes()
    assert import_data(source, database) == 3
    assert import_data(source, database) == 3
    assert source.read_bytes() == before
    rows = fetch_all("catalog_price", (12, 12), database)
    assert isinstance(rows[0], sqlite3.Row)
    assert [r["id"] for r in rows] == [12, 9, 5]
    assert rows[2]["category"] == "музей"
    assert len(fetch_all("category_list", (), database)) == 2


def test_constraints_and_foreign_keys(source, tmp_path):
    database = tmp_path / "test.sqlite"
    import_data(source, database)
    with closing(get_connection(database, create=True)) as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        for sql in [
            "UPDATE attractions SET category_id=999 WHERE id=5",
            "UPDATE attractions SET price=-1 WHERE id=5",
            "UPDATE attractions SET open_hour=23, close_hour=5 WHERE id=5",
            "UPDATE attractions SET name=NULL WHERE id=5",
            "DELETE FROM categories WHERE name='музей'",
        ]:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(sql)
            conn.rollback()


def test_aggregates_and_having_include_empty_category(source, tmp_path):
    database = tmp_path / "test.sqlite"
    import_data(source, database)
    with closing(get_connection(database, create=True)) as conn:
        conn.execute("INSERT INTO categories(name,name_key) VALUES (?, ?)",
                     ("театр", "театр"))
        conn.commit()
    overview = fetch_one("overview", (), database)
    assert overview["total"] == 3
    assert overview["described"] == 1
    assert overview["avg_price"] == 100
    assert overview["total_price"] == 300
    assert fetch_one("free_count", (), database)["total"] == 1
    stats = fetch_all("category_stats", (), database)
    assert stats[-1]["places_count"] == 0
    assert stats[-1]["avg_price"] is None
    popular = fetch_all("popular_categories", (1,), database)
    assert [row["name"] for row in popular] == ["музей"]
    assert fetch_all("popular_categories", (10,), database) == []
    assert len(fetch_all("price_groups", (), database)) == 2


def test_invalid_import_leaves_existing_data(source, tmp_path):
    database = tmp_path / "test.sqlite"
    import_data(source, database)
    records = json.loads(source.read_text(encoding="utf-8"))
    records[0]["name"] = "Не сохранять"
    records[1]["price"] = -5
    source.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(ValueError):
        import_data(source, database)
    assert fetch_one("detail", (12, 12, 5), database)["name"] == "Музей"


def test_import_transaction_rolls_back(source, tmp_path):
    database = tmp_path / "test.sqlite"
    import_data(source, database)
    with closing(get_connection(database, create=True)) as conn:
        conn.execute("""CREATE TRIGGER reject_update BEFORE UPDATE
                        ON attractions WHEN NEW.id = 9
                        BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
        conn.commit()
    records = json.loads(source.read_text(encoding="utf-8"))
    records[0]["name"] = "Не сохранять"
    source.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(sqlite3.IntegrityError):
        import_data(source, database)
    assert fetch_one("detail", (12, 12, 5), database)["name"] == "Музей"


def test_missing_database_not_silently_created(tmp_path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        get_connection(path)
    assert not path.exists()


def test_sql_minimum_and_parameterized_search(source, tmp_path):
    database = tmp_path / "test.sqlite"
    import_data(source, database)
    queries = load_queries()
    assert len(queries) >= 10
    for keyword in ["WHERE", "JOIN", "COUNT(", "GROUP BY"]:
        assert sum(keyword in sql.upper() for sql in queries.values()) >= 2
    params = (12, 12, "' OR 1=1 --", "' OR 1=1 --",
              None, None, None, None, None, None, None)
    assert fetch_all("search", params, database) == []
    assert fetch_one("overview", (), database)["total"] == 3
    preview = fetch_all("home_preview", (12, 12, 1, 1), database)
    assert [r["id"] for r in preview] == [9]


def test_empty_database_aggregates(tmp_path):
    source = tmp_path / "empty.json"
    source.write_text("[]", encoding="utf-8")
    database = tmp_path / "empty.sqlite"
    import_data(source, database)
    row = fetch_one("overview", (), database)
    assert row["total"] == 0
    assert row["avg_price"] is None
    assert row["total_price"] == 0
