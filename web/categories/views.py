from django.http import Http404
from django.shortcuts import render

from web import services
from web.categories.models import Category


def category_list(request):
    return render(request, "categories/list.html", {
        "categories": services.category_stats(),
    })


def category_detail(request, category_name):
    try:
        category = services.get_category(category_name)
    except Category.DoesNotExist:
        raise Http404("Категория не найдена")
    return render(request, "categories/detail.html", {
        "category": category,
        **services.paginate(request, services.category_places(category)),
    })
