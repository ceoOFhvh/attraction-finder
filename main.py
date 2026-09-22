"""Сервис поиска достопримечательностей — точка запуска программы."""

from typing import List

from attractions import (
    Attraction,
    add_attraction,
    filter_by_category,
    find_attraction,
    sort_attractions_by_price,
)
from storage import load_attractions, save_attractions
from utils import input_int

DATA_FILE = "data/attractions.json"


def show_attractions(attractions: List[Attraction]) -> None:
    """Вывести список достопримечательностей.

    Каждый объект сам определяет своё строковое представление
    через __str__(), поэтому main.py не формирует строку вручную.
    """
    if not attractions:
        print("Список пуст.")
        return
    for item in attractions:
        print(item)


def main() -> None:
    """Точка запуска приложения: меню и обработка выбора пользователя."""
    attractions = load_attractions(DATA_FILE)

    menu = """
=== Сервис поиска достопримечательностей ===
1. Показать все достопримечательности
2. Найти по названию
3. Отфильтровать по категории
4. Отсортировать по цене
5. Рассчитать цену со скидкой
6. Добавить достопримечательность
0. Выход
"""

    while True:
        print(menu)
        choice = input("Выберите действие: ")

        if choice == "1":
            show_attractions(attractions)

        elif choice == "2":
            query = input("Название или часть названия: ")
            show_attractions(find_attraction(attractions, query))

        elif choice == "3":
            category = input("Категория (например, музей): ")
            show_attractions(filter_by_category(attractions, category))

        elif choice == "4":
            show_attractions(sort_attractions_by_price(attractions))

        elif choice == "5":
            base_price = input_int("Базовая цена билета: ")
            answer = input("Есть скидка? (да/нет): ").strip().lower()
            has_discount = answer == "да"
            final_price = Attraction.calculate_price(base_price, has_discount)
            print(f"Итоговая цена: {final_price} руб.")

        elif choice == "6":
            name = input("Название: ")
            category = input("Категория: ")
            open_hour = input_int("Час открытия: ")
            close_hour = input_int("Час закрытия: ")
            price = input_int("Цена билета: ")
            add_attraction(
                attractions, name, category, open_hour, close_hour, price,
            )
            save_attractions(DATA_FILE, attractions)
            print("Достопримечательность добавлена и сохранена.")

        elif choice == "0":
            print("До встречи!")
            break

        else:
            print("Такого пункта меню нет, попробуйте ещё раз.")


if __name__ == "__main__":
    main()
