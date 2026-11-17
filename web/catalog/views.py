from django.shortcuts import render

from web import services
from web.catalog.forms import SearchForm, SORTS
from web.catalog.models import Attraction


def attraction_list(request):
    sort = request.GET.get("sort", "name")
    if sort not in SORTS:
        sort = "name"
    context = services.paginate(request, services.get_attractions(sort))
    return render(request, "catalog/list.html", {**context, "sort": sort})


def attraction_detail(request, attraction_id):
    try:
        attraction = services.get_attraction(attraction_id)
    except Attraction.DoesNotExist:
        attraction = None
    return render(
        request, "catalog/detail.html", {"attraction": attraction},
        status=404 if attraction is None else 200,
    )


def free_places(request):
    return render(request, "catalog/free.html",
                  services.paginate(request, services.free_places()))


def search(request):
    form = SearchForm(request.GET)
    valid = form.is_valid()
    places = (services.search_places(form.cleaned_data) if valid
              else Attraction.objects.none())
    context = services.paginate(request, places)
    return render(request, "catalog/search.html", {
        **context, "form": form, "errors": form.errors,
    }, status=200 if valid else 400)


def statistics(request):
    error = ""
    value = request.GET.get("threshold", "1")
    try:
        threshold = int(value)
        if not 0 <= threshold <= 1000000:
            raise ValueError
    except ValueError:
        threshold = 1
        error = "Введите целое число от 0 до 1000000."
    return render(request, "catalog/statistics.html", {
        "overview": services.overview(),
        "free": {"total": services.free_count()},
        "categories": services.category_stats(),
        "price_groups": services.price_groups(),
        "popular": services.popular_categories(threshold),
        "opening_hours": services.opening_hours(),
        "threshold": value, "error": error,
    }, status=400 if error else 200)
