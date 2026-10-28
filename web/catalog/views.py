import math

from django.shortcuts import render

from db.queries import fetch_all, fetch_one
from web.services import get_attractions, hour_parameters


def attraction_list(request):
    sort = "price" if request.GET.get("sort") == "price" else "name"
    return render(request, "catalog/list.html", {
        "attractions": get_attractions(sort), "sort": sort,
    })


def attraction_detail(request, attraction_id):
    attraction = fetch_one("detail", hour_parameters() + (attraction_id,))
    return render(
        request, "catalog/detail.html", {"attraction": attraction},
        status=404 if attraction is None else 200,
    )


def free_places(request):
    return render(request, "catalog/free.html", {
        "attractions": fetch_all("free_places", hour_parameters()),
    })


def search(request):
    values = {key: request.GET.get(key, "").strip()
              for key in ("q", "category", "budget", "hour")}
    categories = fetch_all("category_list")
    errors = []
    try:
        category = int(values["category"]) if values["category"] else None
        budget = float(values["budget"]) if values["budget"] else None
        hour = int(values["hour"]) if values["hour"] else None
        category_ids = [c["id"] for c in categories]
        if category is not None and category not in category_ids:
            errors.append("Выберите категорию из списка.")
        if budget is not None and (not math.isfinite(budget) or budget < 0):
            errors.append("Бюджет должен быть неотрицательным числом.")
        if hour is not None and not 0 <= hour <= 23:
            errors.append("Час посещения должен быть от 0 до 23.")
    except (ValueError, OverflowError):
        errors.append("Проверьте числовые значения категории, бюджета и часа.")
    attractions = []
    if not errors:
        query = values["q"].casefold()
        parameters = hour_parameters() + (
            query, query, category, category, budget, budget, hour, hour, hour,
        )
        attractions = fetch_all("search", parameters)
    return render(request, "catalog/search.html", {
        "attractions": attractions, "categories": categories,
        "values": values, "errors": errors,
    }, status=400 if errors else 200)


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
        "overview": fetch_one("overview"),
        "free": fetch_one("free_count"),
        "categories": fetch_all("category_stats"),
        "price_groups": fetch_all("price_groups"),
        "popular": fetch_all("popular_categories", (threshold,)),
        "threshold": value, "error": error,
    }, status=400 if error else 200)
