"""Связь Django с сохранённой предметной моделью ПР3."""
from django.conf import settings

from core.storage import load_attractions


def get_attractions():
    """Читать JSON заново при каждом запросе, не меняя его содержимое."""
    return load_attractions(settings.DATA_FILE)


def get_categories(attractions):
    """Собрать категории из реальных объектов, без отдельного хранилища."""
    groups = {}
    for item in attractions:
        name = item.category.strip()
        if not name:
            continue
        key = name.casefold()
        group = groups.setdefault(key, {"name": name, "items": []})
        group["items"].append(item)
    return sorted(groups.values(), key=lambda group: group["name"].casefold())
