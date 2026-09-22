from datetime import datetime
from unittest.mock import patch

from attractions import (
    Attraction,
    add_attraction,
    filter_by_category,
    find_attraction,
    sort_attractions_by_price,
)


def test_attraction_creation():
    attraction = Attraction(1, "Городской музей", "музей", 10, 18, 350.0)
    assert attraction.id == 1
    assert attraction.name == "Городской музей"
    assert attraction.category == "музей"
    assert attraction.open_hour == 10
    assert attraction.close_hour == 18
    assert attraction.price == 350.0


def test_attraction_str_contains_name():
    attraction = Attraction(1, "Городской музей", "музей", 10, 18, 350.0)
    assert "Городской музей" in str(attraction)


def test_attraction_is_open_now():
    attraction = Attraction(1, "Музей", "музей", 10, 18, 300.0)
    with patch("attractions.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 9, 22, 12, 0)
        assert attraction.is_open_now()

        mock_datetime.now.return_value = datetime(2026, 9, 22, 20, 0)
        assert not attraction.is_open_now()


def test_attraction_from_data_and_to_dict():
    data = {
        "id": 5,
        "name": "Центральный парк",
        "category": "парк",
        "open_hour": 6,
        "close_hour": 22,
        "price": 0.0,
    }
    attraction = Attraction.from_data(data)
    assert attraction.id == 5
    assert attraction.name == "Центральный парк"
    assert attraction.to_dict() == data


def test_add_attraction():
    attractions: list[Attraction] = []
    attraction = add_attraction(
        attractions, "Аудитория 301", "музей", 10, 18, 350.0,
    )
    assert len(attractions) == 1
    assert attractions[0] is attraction
    assert isinstance(attraction, Attraction)


def test_find_attraction():
    attractions: list[Attraction] = []
    add_attraction(attractions, "Городской музей", "музей", 10, 18, 350.0)
    assert find_attraction(attractions, "музей")


def test_filter_by_category():
    attractions: list[Attraction] = []
    add_attraction(attractions, "Парк culture", "парк", 6, 23, 0.0)
    add_attraction(attractions, "Музей", "музей", 10, 18, 300.0)
    result = filter_by_category(attractions, "парк")
    assert len(result) == 1
    assert result[0].category == "парк"


def test_sort_attractions_by_price():
    attractions: list[Attraction] = []
    add_attraction(attractions, "Дорогой музей", "музей", 10, 18, 500.0)
    add_attraction(attractions, "Бесплатный парк", "парк", 6, 23, 0.0)
    result = sort_attractions_by_price(attractions)
    assert result[0].price == 0.0


def test_calculate_price_with_discount():
    assert Attraction.calculate_price(100.0, True, 20) == 80.0


def test_calculate_price_without_discount():
    assert Attraction.calculate_price(100.0, False) == 100.0
