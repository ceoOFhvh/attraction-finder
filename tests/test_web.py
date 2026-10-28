"""Проверки страниц, данных JSON и поведения шаблонов."""
import json
from unittest.mock import patch

import pytest

from db.database import get_connection
from db.import_json import import_data
from django.test import override_settings
from django.urls import reverse


@pytest.fixture
def dataset(tmp_path, settings):
    records = [
        {"id": 1, "name": "Музей", "category": "музей",
         "open_hour": 10, "close_hour": 18, "price": 350.0},
        {"id": 2, "name": "Парк", "category": "парк",
         "open_hour": 6, "close_hour": 23, "price": 0.0},
    ]
    path = tmp_path / "attractions.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    settings.DATA_FILE = path
    settings.SQLITE_PATH = tmp_path / "web.sqlite"
    import_data(path, settings.SQLITE_PATH)
    return path


@pytest.mark.parametrize("name,args,template", [
    ("homepage:index", [], "homepage/index.html"),
    ("catalog:list", [], "catalog/list.html"),
    ("catalog:detail", [1], "catalog/detail.html"),
    ("categories:list", [], "categories/list.html"),
    ("categories:detail", ["музей"], "categories/detail.html"),
])
def test_pages(client, dataset, name, args, template):
    response = client.get(reverse(name, args=args))
    assert response.status_code == 200
    names = [item.name for item in response.templates]
    assert template in names
    assert "base.html" in names
    assert "includes/navigation.html" in names
    assert b"/static/css/style.css" in response.content


@pytest.mark.parametrize("path", [
    "/attractions/no-number/",
    "/categories/unknown/", "/missing/",
])
def test_not_found(client, dataset, path):
    with override_settings(DEBUG=False):
        response = client.get(path)
    assert response.status_code == 404
    assert "Здесь пока ничего нет" in response.content.decode()


@pytest.mark.parametrize("url,expected", [
    ("/", "В каталоге пока нет"),
    ("/attractions/", "В каталоге пока нет"),
    ("/categories/", "Категории появятся"),
])
def test_empty_lists(client, dataset, settings, url, expected):
    conn = get_connection(settings.SQLITE_PATH, create=True)
    try:
        conn.execute("DELETE FROM attractions")
        conn.execute("DELETE FROM categories")
        conn.commit()
    finally:
        conn.close()
    response = client.get(url)
    assert response.status_code == 200
    assert expected in response.content.decode()


def test_data_reloaded_and_escaped(client, dataset, settings):
    records = json.loads(dataset.read_text(encoding="utf-8"))
    records[0]["name"] = "<script>alert(1)</script>"
    dataset.write_text(json.dumps(records), encoding="utf-8")
    import_data(dataset, settings.SQLITE_PATH)
    html = client.get("/attractions/1/").content.decode()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_price_sort_and_free_label(client, dataset):
    response = client.get("/attractions/?sort=price")
    assert [item["id"] for item in response.context["attractions"]] == [2, 1]
    assert "Бесплатно" in response.content.decode()


def test_category_contains_only_matching_places(client, dataset):
    response = client.get(reverse("categories:detail", args=["МУЗЕЙ"]))
    assert response.status_code == 200
    assert [item["id"] for item in response.context["attractions"]] == [1]


@pytest.mark.parametrize("hour,label", [
    (10, "Открыто сейчас"), (17, "Открыто сейчас"),
    (18, "Сейчас закрыто"), (9, "Сейчас закрыто"),
])
def test_open_status(client, dataset, hour, label):
    with patch("web.services.current_hour", return_value=hour):
        html = client.get("/attractions/1/").content.decode()
    assert label in html


def test_requests_do_not_modify_json(client, dataset):
    before = dataset.read_bytes()
    for path in ["/", "/attractions/", "/attractions/1/", "/categories/"]:
        client.get(path)
    assert dataset.read_bytes() == before


def test_web_keeps_working_without_source_json(client, dataset):
    dataset.unlink()
    response = client.get("/attractions/")
    assert response.status_code == 200
    assert len(response.context["attractions"]) == 2


def test_static_assets_are_found():
    from django.contrib.staticfiles import finders

    assets = ["css/style.css", "js/main.js", "img/logo.svg", "img/city.svg"]
    for asset in assets:
        assert finders.find(asset)


@pytest.mark.parametrize("debug", [True, False])
def test_missing_attraction_uses_detail_template(client, dataset, debug):
    with override_settings(DEBUG=debug):
        response = client.get("/attractions/999/")
    assert response.status_code == 404
    assert response.context["attraction"] is None
    assert "catalog/detail.html" in [t.name for t in response.templates]
    html = response.content.decode()
    assert "404 — Достопримечательность не найдена" in html
    assert "Traceback" not in response.content.decode()


@pytest.mark.parametrize("url,template", [
    ("/attractions/search/", "catalog/search.html"),
    ("/attractions/free/", "catalog/free.html"),
    ("/attractions/statistics/", "catalog/statistics.html"),
])
def test_new_pages(client, dataset, url, template):
    response = client.get(url)
    assert response.status_code == 200
    assert template in [t.name for t in response.templates]


@pytest.mark.parametrize("params,ids", [
    ({"q": "МУЗ"}, [1]),
    ({"budget": "0"}, [2]),
    ({"hour": "18", "budget": "400"}, [2]),
    ({"hour": "10", "q": "музей"}, [1]),
    ({"hour": "3"}, []),
    ({"q": "' OR 1=1 --"}, []),
])
def test_search_filters(client, dataset, params, ids):
    response = client.get("/attractions/search/", params)
    assert response.status_code == 200
    assert [r["id"] for r in response.context["attractions"]] == ids


@pytest.mark.parametrize("params", [
    {"hour": "24"}, {"hour": "abc"}, {"budget": "-1"},
    {"budget": "nan"}, {"budget": "inf"}, {"category": "999"},
])
def test_invalid_search_input(client, dataset, params):
    response = client.get("/attractions/search/", params)
    assert response.status_code == 400
    assert response.context["errors"]


def test_statistics_and_free_page(client, dataset):
    response = client.get("/attractions/statistics/")
    assert response.context["overview"]["total"] == 2
    assert response.context["overview"]["avg_price"] == 175
    assert response.context["free"]["total"] == 1
    assert len(response.context["popular"]) == 0
    response = client.get("/attractions/statistics/?threshold=0")
    assert len(response.context["popular"]) == 2
    response = client.get("/attractions/free/")
    assert [r["id"] for r in response.context["attractions"]] == [2]


def test_invalid_statistics_input(client, dataset):
    response = client.get("/attractions/statistics/?threshold=abc")
    assert response.status_code == 400
    assert response.context["error"]


def test_database_updates_appear_without_reimport(client, dataset, settings):
    conn = get_connection(settings.SQLITE_PATH, create=True)
    try:
        conn.execute("UPDATE attractions SET name=? WHERE id=?",
                     ("Название из SQLite", 1))
        conn.commit()
    finally:
        conn.close()
    html = client.get("/attractions/1/").content.decode()
    assert "Название из SQLite" in html
    assert "Название из SQLite" not in dataset.read_text(encoding="utf-8")
