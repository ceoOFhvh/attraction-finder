from django.shortcuts import render
from django.utils import timezone

from db.queries import fetch_all, fetch_one
from web.services import hour_parameters


def index(request):
    return render(request, "homepage/index.html", {
        "attractions": fetch_all("home_preview", hour_parameters() + (3, 0)),
        "categories": fetch_all("category_list"),
        "overview": fetch_one("overview"),
        "today": timezone.localdate(),
    })


def not_found(request, exception):
    return render(request, "404.html", status=404)
