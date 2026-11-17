"""Безопасная и повторяемая демонстрация CRUD для защиты."""
from decimal import Decimal
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.deletion import ProtectedError

from web.catalog.models import Attraction
from web.categories.models import Category


class Command(BaseCommand):
    help = "Демонстрация CRUD и PROTECT с откатом изменений"

    def handle(self, *args, **options):
        before = Attraction.objects.count()
        with transaction.atomic():
            category = Category.objects.create(name=f"Демо {uuid4().hex[:8]}")
            place = Attraction.objects.create(
                name="Учебный парк", category=category,
                open_hour=6, close_hour=23, price=0,
            )
            self.stdout.write(f"CREATE: создано место #{place.pk}: {place}")
            saved = Attraction.objects.select_related("category").get(
                pk=place.pk,
            )
            self.stdout.write(f"READ: {saved.name}; {saved.category}")
            saved.price = Decimal("100.00")
            saved.save(update_fields=["price"])
            saved.refresh_from_db()
            self.stdout.write(f"UPDATE: цена стала {saved.price}")
            try:
                category.delete()
            except ProtectedError:
                self.stdout.write("PROTECT: категорию с местом удалить нельзя")
            saved.delete()
            self.stdout.write("DELETE: учебное место удалено")
            transaction.set_rollback(True)
        after = Attraction.objects.count()
        self.stdout.write(f"Откат: было {before}, осталось {after} мест.")
