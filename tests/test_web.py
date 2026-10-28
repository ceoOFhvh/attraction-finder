"""Проверки страниц, данных JSON и поведения шаблонов."""
import json
from datetime import datetime
from unittest.mock import patch

import pytest
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
def test_empty_lists(client, dataset, url, expected):
    dataset.write_text("[]", encoding="utf-8")
    response = client.get(url)
    assert response.status_code == 200
    assert expected in response.content.decode()


def test_data_reloaded_and_escaped(client, dataset):
    records = json.loads(dataset.read_text(encoding="utf-8"))
    records[0]["name"] = "<script>alert(1)</script>"
    dataset.write_text(json.dumps(records), encoding="utf-8")
    html = client.get("/attractions/1/").content.decode()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_price_sort_and_free_label(client, dataset):
    response = client.get("/attractions/?sort=price")
    assert [item.id for item in response.context["attractions"]] == [2, 1]
    assert "Бесплатно" in response.content.decode()


def test_category_contains_only_matching_places(client, dataset):
    response = client.get(reverse("categories:detail", args=["МУЗЕЙ"]))
    assert response.status_code == 200
    assert [item.id for item in response.context["category"]["items"]] == [1]


@pytest.mark.parametrize("hour,label", [
    (10, "Открыто сейчас"), (17, "Открыто сейчас"),
    (18, "Сейчас закрыто"), (9, "Сейчас закрыто"),
])
def test_open_status(client, dataset, hour, label):
    with patch("core.attractions.datetime") as clock:
        clock.now.return_value = datetime(2026, 10, 13, hour)
        html = client.get("/attractions/1/").content.decode()
    assert label in html


def test_requests_do_not_modify_json(client, dataset):
    before = dataset.read_bytes()
    for path in ["/", "/attractions/", "/attractions/1/", "/categories/"]:
        client.get(path)
    assert dataset.read_bytes() == before


def test_missing_file_is_empty_catalog(client, dataset):
    dataset.unlink()
    response = client.get("/attractions/")
    assert response.status_code == 200
    assert len(response.context["attractions"]) == 0


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
