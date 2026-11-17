from django.shortcuts import render
from django.utils import timezone

from web import services


def index(request):
    return render(request, "homepage/index.html", {
        "attractions": services.home_preview(),
        "categories": services.category_list(),
        "overview": services.overview(), "today": timezone.localdate(),
    })


def not_found(request, exception):
    return render(request, "404.html", status=404)
