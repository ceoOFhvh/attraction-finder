from django import forms

from web.categories.models import Category

SORTS = {
    "name": ("search_name", "pk"),
    "price": ("price", "search_name", "pk"),
    "price_desc": ("-price", "search_name", "pk"),
    "category": ("category__name_key", "search_name", "pk"),
}
SORT_LABELS = [("name", "По названию"), ("price", "Сначала дешевле"),
               ("price_desc", "Сначала дороже"), ("category", "По категории")]


class SearchForm(forms.Form):
    q = forms.CharField(label="Название", required=False, max_length=200)
    text = forms.CharField(label="Название или описание", required=False,
                           max_length=200)
    category = forms.ModelChoiceField(
        label="Категория", queryset=Category.objects.all(), required=False,
        empty_label="Все категории",
    )
    budget = forms.DecimalField(label="Бюджет до, ₽", required=False,
                                min_value=0, max_digits=10, decimal_places=2)
    hour = forms.IntegerField(label="Час посещения", required=False,
                              min_value=0, max_value=23)
    payment = forms.ChoiceField(
        label="Стоимость входа", required=False,
        choices=[("", "Любая"), ("free", "Бесплатно"), ("paid", "Платно")],
    )
    sort = forms.ChoiceField(label="Сортировка", required=False,
                             choices=SORT_LABELS)
