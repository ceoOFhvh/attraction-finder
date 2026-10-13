from django.shortcuts import render
from django.utils import timezone

from web.services import get_attractions, get_categories


def index(request):
    attractions = get_attractions()
    context = {
        "attractions": attractions,
        "categories": get_categories(attractions),
        "today": timezone.localdate(),
    }
    return render(request, "homepage/index.html", context)


def not_found(request, exception):
    return render(request, "404.html", status=404)
