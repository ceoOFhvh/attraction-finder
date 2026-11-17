from django.db import models


class Category(models.Model):
    name = models.CharField("Название", max_length=120)
    name_key = models.CharField(max_length=120, unique=True, editable=False)

    class Meta:
        ordering = ["name_key", "pk"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        constraints = [models.CheckConstraint(
            condition=~models.Q(name=""), name="category_name_not_empty",
        )]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.name_key = self.name.casefold()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                "name", "name_key",
            }
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
