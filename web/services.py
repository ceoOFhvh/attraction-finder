"""Запросы ПР9: сайт получает данные только через Django ORM."""
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Avg, Case, CharField, Count, F, Max, Min
from django.db.models import Q, Sum, Value, When
from django.utils import timezone

from web.catalog.forms import SORTS
from web.catalog.models import Attraction
from web.categories.models import Category


def current_hour():
    return timezone.localtime().hour


def get_attractions(sort="name"):
    return Attraction.objects.select_related("category").order_by(
        *SORTS.get(sort, SORTS["name"])
    )


def get_attraction(pk):
    return Attraction.objects.select_related("category").get(pk=pk)


def category_list():
    return Category.objects.all()


def get_category(name):
    return Category.objects.get(name_key=name.casefold())


def category_places(category):
    return category.attractions.select_related("category").all()


def free_places():
    return get_attractions().filter(price=0)


def paid_places(queryset):
    return queryset.exclude(price=0)


def by_category(queryset, category):
    return queryset.filter(category__name_key=category.name_key)


def within_budget(queryset, budget):
    return queryset.filter(price__lte=budget)


def open_at(queryset, hour):
    return queryset.filter(open_hour__lte=hour, close_hour__gt=hour)


def search_name(queryset, query):
    return queryset.filter(search_name__icontains=query.casefold())


def search_text(queryset, query):
    query = query.casefold()
    return queryset.filter(Q(search_name__icontains=query)
                           | Q(search_description__icontains=query))


def search_places(data):
    result = get_attractions(data.get("sort") or "name")
    if data.get("q"):
        result = search_name(result, data["q"])
    if data.get("text"):
        result = search_text(result, data["text"])
    if data.get("category"):
        result = by_category(result, data["category"])
    if data.get("budget") is not None:
        result = within_budget(result, data["budget"])
    if data.get("hour") is not None:
        result = open_at(result, data["hour"])
    if data.get("payment") == "free":
        result = result.filter(price=0)
    elif data.get("payment") == "paid":
        result = paid_places(result)
    return result


def overview():
    return Attraction.objects.aggregate(
        total=Count("pk"), described=Count("description"),
        min_price=Min("price"), max_price=Max("price"),
        avg_price=Avg("price"), total_price=Sum("price", default=0),
    )


def free_count():
    return Attraction.objects.filter(price=0).count()


def category_stats():
    return Category.objects.annotate(
        places_count=Count("attractions"),
        min_price=Min("attractions__price"),
        max_price=Max("attractions__price"),
        avg_price=Avg("attractions__price"),
    )


def popular_categories(threshold):
    return category_stats().filter(places_count__gt=threshold)


def price_groups():
    return Attraction.objects.order_by().annotate(label=Case(
        When(price=0, then=Value("Бесплатно")), default=Value("Платно"),
        output_field=CharField(),
    )).values("label").annotate(
        places_count=Count("pk"), avg_price=Avg("price"),
    ).order_by("label")


def opening_hours():
    return Attraction.objects.annotate(
        category_name=F("category__name"),
        hours_open=F("close_hour") - F("open_hour"),
    ).values("id", "name", "category_name", "hours_open")


def home_preview():
    return get_attractions().order_by("pk")[:3]


def paginate(request, queryset):
    page = Paginator(queryset, settings.CATALOG_PAGE_SIZE).get_page(
        request.GET.get("page")
    )
    return {"attractions": page.object_list, "page_obj": page}
