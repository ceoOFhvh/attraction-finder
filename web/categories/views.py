from django.http import Http404
from django.shortcuts import render

from web.services import get_attractions, get_categories


def category_list(request):
    return render(request, "categories/list.html", {
        "categories": get_categories(get_attractions()),
    })


def category_detail(request, category_name):
    category = next(
        (group for group in get_categories(get_attractions())
         if group["name"].casefold() == category_name.casefold()),
        None,
    )
    if category is None:
        raise Http404("Категория не найдена")
    return render(request, "categories/detail.html", {"category": category})
