from datetime import datetime
from typing import List


class Attraction:
    """Достопримечательность города, доступная для поиска и просмотра."""

    def __init__(
        self,
        attraction_id: int,
        name: str,
        category: str,
        open_hour: int,
        close_hour: int,
        price: float,
    ) -> None:
        """Создать объект достопримечательности и сохранить его данные."""
        self.id = attraction_id
        self.name = name
        self.category = category
        self.open_hour = open_hour
        self.close_hour = close_hour
        self.price = price

    def is_open_now(self) -> bool:
        """Проверить, открыта ли достопримечательность в текущий момент."""
        current_hour = datetime.now().hour
        return self.open_hour <= current_hour < self.close_hour

    @staticmethod
    def calculate_price(
        base_price: float,
        has_discount: bool,
        discount_percent: int = 20,
    ) -> float:

        if has_discount:
            return round(base_price - base_price * discount_percent / 100, 2)
        return round(base_price, 2)

    @classmethod
    def from_data(cls, data: dict) -> "Attraction":
        """Создать объект Attraction из словаря данных (например, из JSON)."""
        return cls(
            attraction_id=data["id"],
            name=data["name"],
            category=data["category"],
            open_hour=data["open_hour"],
            close_hour=data["close_hour"],
            price=data["price"],
        )

    def to_dict(self) -> dict:
        """Преобразовать объект в словарь для сохранения в JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "open_hour": self.open_hour,
            "close_hour": self.close_hour,
            "price": self.price,
        }

    def __str__(self) -> str:
        """Вернуть удобное строковое представление достопримечательности."""
        status = "открыто" if self.is_open_now() else "закрыто"
        return (
            f"{self.id}. {self.name} | {self.category} | "
            f"{self.open_hour}:00-{self.close_hour}:00 | "
            f"{self.price} руб. | сейчас {status}"
        )


def add_attraction(
    attractions: List[Attraction],
    name: str,
    category: str,
    open_hour: int,
    close_hour: int,
    price: float,
) -> Attraction:
    """Создать объект Attraction, добавить его в коллекцию и вернуть его."""
    new_id = max((item.id for item in attractions), default=0) + 1
    attraction = Attraction(
        new_id, name, category, open_hour, close_hour, price,
    )
    attractions.append(attraction)
    return attraction


def find_attraction(
    attractions: List[Attraction],
    query: str,
) -> List[Attraction]:
    """Найти достопримечательности, в названии которых встречается query."""
    query = query.lower()
    return [item for item in attractions if query in item.name.lower()]


def filter_by_category(
    attractions: List[Attraction],
    category: str,
) -> List[Attraction]:
    """Отобрать достопримечательности выбранной категории."""
    category = category.lower()
    return [item for item in attractions if item.category.lower() == category]


def sort_attractions_by_price(
    attractions: List[Attraction],
) -> List[Attraction]:
    """Вернуть достопримечательности, отсортированные по цене билета."""
    return sorted(attractions, key=lambda item: item.price)
