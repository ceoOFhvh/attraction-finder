from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Attraction(models.Model):
    name = models.CharField("Название", max_length=200)
    search_name = models.CharField(max_length=200, editable=False)
    description = models.TextField("Описание", blank=True, null=True)
    search_description = models.TextField(blank=True, editable=False)
    category = models.ForeignKey(
        "categories.Category", on_delete=models.PROTECT,
        related_name="attractions", verbose_name="Категория",
    )
    open_hour = models.PositiveSmallIntegerField(
        "Час открытия", validators=[MaxValueValidator(23)],
    )
    close_hour = models.PositiveSmallIntegerField(
        "Час закрытия",
        validators=[MinValueValidator(1), MaxValueValidator(24)],
    )
    price = models.DecimalField(
        "Цена", max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0)], db_index=True,
    )

    class Meta:
        ordering = ["search_name", "pk"]
        verbose_name = "Достопримечательность"
        verbose_name_plural = "Достопримечательности"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0), name="attraction_price_gte0",
            ),
            models.CheckConstraint(
                condition=models.Q(open_hour__lte=23, close_hour__lte=24,
                                   close_hour__gt=models.F("open_hour")),
                name="attraction_valid_hours",
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""), name="attraction_name_not_empty",
            ),
        ]

    def clean(self):
        super().clean()
        if (self.open_hour is not None and self.close_hour is not None
                and self.open_hour >= self.close_hour):
            raise ValidationError("Закрытие должно быть позже открытия.")

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.search_name = self.name.casefold()
        self.search_description = (self.description or "").casefold()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                "name", "search_name", "search_description",
            }
        super().save(*args, **kwargs)

    @property
    def is_open_now(self):
        from web.services import current_hour

        return self.open_hour <= current_hour() < self.close_hour

    def __str__(self):
        return self.name
