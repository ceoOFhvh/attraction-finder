from django.shortcuts import render

from core.attractions import sort_attractions_by_price
from web.services import get_attractions


def attraction_list(request):
    attractions = get_attractions()
    sort = request.GET.get("sort", "name")
    if sort == "price":
        attractions = sort_attractions_by_price(attractions)
    else:
        sort = "name"
        attractions = sorted(
            attractions, key=lambda item: item.name.casefold(),
        )
    return render(request, "catalog/list.html", {
        "attractions": attractions, "sort": sort,
    })


def attraction_detail(request, attraction_id):
    attraction = next(
        (item for item in get_attractions() if item.id == attraction_id),
        None,
    )
    return render(
        request,
        "catalog/detail.html",
        {"attraction": attraction},
        status=404 if attraction is None else 200,
    )
