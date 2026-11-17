"""ПР9: миграции, перенос, связи, CRUD, запросы и пагинация."""
import io
import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from db.import_json import import_data
from web import services
from web.catalog.models import Attraction
from web.categories.models import Category

pytestmark = pytest.mark.django_db


@pytest.fixture
def places():
    museum = Category.objects.create(name="Музей")
    park = Category.objects.create(name="Парк")
    Category.objects.create(name="Театр")
    for number, price in enumerate([100, 200, 300, 400, 0], 1):
        Attraction.objects.create(
            id=number, name=f"Место {number}",
            category=park if price == 0 else museum,
            open_hour=6, close_hour=23, price=price,
            description="Редкие картины" if number == 2 else None,
        )


def test_crud_and_normalized_fields(places):
    obj = Attraction.objects.get(pk=1)
    obj.name = "Новое ИМЯ"
    obj.description = "ПРОГУЛКА"
    obj.save(update_fields=["name", "description"])
    obj.refresh_from_db()
    assert obj.search_name == "новое имя"
    assert obj.search_description == "прогулка"
    obj.delete()
    assert not Attraction.objects.filter(pk=1).exists()


def test_fk_protect_and_reverse_relation(places):
    category = Category.objects.get(name_key="музей")
    assert category.attractions.count() == 4
    with pytest.raises(ProtectedError):
        category.delete()


@pytest.mark.parametrize("changes", [
    {"price": -1}, {"open_hour": 23, "close_hour": 5},
    {"close_hour": 25}, {"category_id": 999}, {"name": ""},
])
def test_database_constraints(places, changes):
    with pytest.raises(IntegrityError), transaction.atomic():
        Attraction.objects.filter(pk=1).update(**changes)
        # SQLite checks foreign keys at commit; force validation in this test.
        from django.db import connection
        connection.check_constraints()


def test_summary_grouping_and_empty_category(places):
    summary = services.overview()
    assert summary == {"total": 5, "described": 1,
                       "min_price": Decimal(0), "max_price": Decimal(400),
                       "avg_price": Decimal(200), "total_price": Decimal(1000)}
    empty = services.category_stats().get(name_key="театр")
    assert empty.places_count == 0 and empty.avg_price is None
    assert services.popular_categories(1).get().name == "Музей"
    assert len(services.price_groups()) == 2
    assert services.opening_hours().get(id=1)["hours_open"] == 17
    hours = services.opening_hours().get(id=1)
    assert hours["category_name"] == "Музей"


def test_select_related_constant_query_count(
        places, django_assert_num_queries):
    with django_assert_num_queries(1):
        names = [obj.category.name for obj in services.get_attractions()]
        assert len(names) == 5


@pytest.mark.parametrize("params,expected", [
    ({"text": "КАРТИНЫ"}, [2]), ({"q": "МЕСТО 1"}, [1]),
    ({"payment": "paid", "budget": "200", "hour": "6"}, [1, 2]),
    ({"payment": "free", "sort": "price_desc"}, [5]),
    ({"hour": "23"}, []), ({"text": "' OR 1=1 --"}, []),
])
def test_search_variants(client, places, params, expected):
    response = client.get("/attractions/search/", params)
    assert response.status_code == 200
    assert [x.pk for x in response.context["attractions"]] == expected


@pytest.mark.parametrize("params", [
    {"sort": "password"}, {"payment": "other"},
    {"budget": "Infinity"}, {"budget": "1e99999"},
    {"hour": "3.5"}, {"q": "x" * 201},
])
def test_invalid_filters(client, places, params):
    response = client.get("/attractions/search/", params)
    assert response.status_code == 400


def test_related_filter_and_pagination(client, places, settings):
    settings.CATALOG_PAGE_SIZE = 2
    category = Category.objects.get(name_key="музей")
    params = {"category": category.pk, "sort": "price_desc", "budget": 400}
    first = client.get("/attractions/search/", params)
    assert [p.pk for p in first.context["attractions"]] == [4, 3]
    assert first.context["page_obj"].paginator.count == 4
    html = first.content.decode()
    for parameter in ("sort=price_desc", "budget=400", "page=2"):
        assert parameter in html
    second = client.get("/attractions/search/", {**params, "page": 2})
    assert [p.pk for p in second.context["attractions"]] == [2, 1]
    assert not second.context["page_obj"].has_next()


@pytest.mark.parametrize("page,number", [("abc", 1), (0, 2), (999, 2)])
def test_bad_page_numbers(client, places, page, number):
    response = client.get("/attractions/", {"page": page})
    assert response.status_code == 200
    assert response.context["page_obj"].number == number


def test_empty_orm_database(client):
    response = client.get("/attractions/statistics/")
    assert response.status_code == 200
    assert response.context["overview"]["total_price"] == 0
    assert response.context["overview"]["avg_price"] is None
    assert client.get("/attractions/search/").status_code == 200


def test_demo_rolls_back(places):
    before = list(Attraction.objects.values())
    categories = list(Category.objects.values())
    for _ in range(2):
        output = io.StringIO()
        call_command("demo_orm", stdout=output)
        assert "PROTECT" in output.getvalue()
    assert list(Attraction.objects.values()) == before
    assert list(Category.objects.values()) == categories


@pytest.fixture
def legacy(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps([
        {"id": 7, "name": "Старый парк", "category": "парк",
         "open_hour": 6, "close_hour": 23, "price": 0},
        {"id": 9, "name": "Старый музей", "category": "музей",
         "open_hour": 10, "close_hour": 18, "price": 123.45},
    ]), encoding="utf-8")
    database = tmp_path / "legacy.sqlite"
    import_data(source, database)
    return database


def test_import_repeat_preserves_ids_source_and_decimal(legacy):
    before = legacy.read_bytes()
    for _ in range(2):
        call_command("import_legacy", source=str(legacy))
    assert Attraction.objects.count() == 2
    assert Attraction.objects.get(pk=9).price == Decimal("123.45")
    assert Attraction.objects.get(pk=7).category.name == "парк"
    assert legacy.read_bytes() == before


def test_import_atomic_rollback(legacy):
    save = Attraction.save

    def fail_second(obj, *args, **kwargs):
        if obj.pk == 9:
            raise ValueError("Имитация ошибки второй записи")
        return save(obj, *args, **kwargs)

    with patch.object(Attraction, "save", fail_second):
        with pytest.raises(CommandError):
            call_command("import_legacy", source=str(legacy))
    assert Attraction.objects.count() == Category.objects.count() == 0


def test_import_missing_source(tmp_path):
    missing = tmp_path / "absent.sqlite"
    with pytest.raises(CommandError):
        call_command("import_legacy", source=str(missing))
    assert not missing.exists()


def test_fixture_roundtrip(places, tmp_path):
    path = tmp_path / "export.json"
    with path.open("w", encoding="utf-8") as stream:
        call_command("dumpdata", "categories", "catalog", stdout=stream)
    Attraction.objects.all().delete()
    Category.objects.all().delete()
    call_command("loaddata", str(path))
    assert Attraction.objects.count() == 5
    assert Attraction.objects.get(pk=2).description == "Редкие картины"
