from django.http import Http404
from django.shortcuts import render

from db.queries import fetch_all, fetch_one
from web.services import hour_parameters


def category_list(request):
    return render(request, "categories/list.html", {
        "categories": fetch_all("category_stats"),
    })


def category_detail(request, category_name):
    category = fetch_one("category_detail", (category_name.casefold(),))
    if category is None:
        raise Http404("Категория не найдена")
    return render(request, "categories/detail.html", {
        "category": category,
        "attractions": fetch_all(
            "category_places", hour_parameters() + (category["id"],),
        ),
    })
