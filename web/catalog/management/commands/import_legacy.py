"""Разовый мост: чтение старой SQLite, запись исключительно через ORM."""
import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from web.catalog.models import Attraction
from web.categories.models import Category


class Command(BaseCommand):
    help = "Перенести категории и места из базы ПР7, сохранив ID и связи"

    def add_arguments(self, parser):
        parser.add_argument("--source", default=str(settings.SQLITE_PATH))

    def handle(self, *args, **options):
        source = Path(options["source"]).resolve()
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if source == target:
            raise CommandError("Источник и новая база должны различаться.")
        try:
            with closing(sqlite3.connect(source.as_uri() + "?mode=ro",
                                         uri=True)) as connection:
                connection.row_factory = sqlite3.Row
                categories = connection.execute(
                    "SELECT id, name FROM categories ORDER BY id"
                ).fetchall()
                places = connection.execute(
                    "SELECT id, name, category_id, open_hour, close_hour, "
                    "price, description FROM attractions ORDER BY id"
                ).fetchall()
            with transaction.atomic():
                for row in categories:
                    if row["id"] <= 0:
                        raise ValueError("ID должен быть больше нуля")
                    obj = Category.objects.filter(pk=row["id"]).first()
                    if obj is None:
                        obj = Category(pk=row["id"])
                    obj.name = row["name"].strip()
                    obj.name_key = obj.name.casefold()
                    obj.full_clean()
                    obj.save()
                ids = {row["id"] for row in categories}
                for row in places:
                    data = dict(row)
                    if data["id"] <= 0 or data["category_id"] not in ids:
                        raise ValueError("Неверный ID или ссылка на категорию")
                    data["price"] = Decimal(str(data["price"]))
                    obj = Attraction.objects.filter(pk=data["id"]).first()
                    if obj is None:
                        obj = Attraction(pk=data["id"])
                    for key, value in data.items():
                        setattr(obj, key, value)
                    obj.name = obj.name.strip()
                    obj.search_name = obj.name.casefold()
                    obj.search_description = (obj.description or "").casefold()
                    obj.full_clean(exclude=["search_description"])
                    obj.save()
        except (sqlite3.Error, ValueError, ValidationError, IntegrityError,
                TypeError, AttributeError) as exc:
            raise CommandError(f"Перенос отменён: {exc}") from exc
        self.stdout.write(self.style.SUCCESS(
            f"Перенесено: категорий {len(categories)}, мест {len(places)}. "
            "ID сохранены. Источник не изменён."
        ))
