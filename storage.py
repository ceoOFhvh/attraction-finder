import json
from typing import List

from attractions import Attraction


def load_attractions(filename: str) -> List[Attraction]:
    """Загрузить достопримечательности из JSON-файла и создать объекты.

    Если файл отсутствует или повреждён — вернуть пустой список,
    не завершая программу аварийно.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Файл {filename} не найден, будет создан новый список.")
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, будет создан новый список.")
        return []

    return [Attraction.from_data(item) for item in data]


def save_attractions(filename: str, attractions: List[Attraction]) -> None:
    """Сохранить список объектов Attraction в JSON-файл."""
    data = [item.to_dict() for item in attractions]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
