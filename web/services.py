"""Получение строк SQLite для представлений Django."""
from datetime import datetime

from db.queries import fetch_all


def current_hour():
    # Сохраняем локальное время сервера, как в консольном методе ПР3.
    return datetime.now().hour


def hour_parameters():
    hour = current_hour()
    return (hour, hour)


def get_attractions(sort="name"):
    query = "catalog_price" if sort == "price" else "catalog_name"
    return fetch_all(query, hour_parameters())
