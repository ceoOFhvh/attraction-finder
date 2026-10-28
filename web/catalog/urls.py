from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.attraction_list, name="list"),
    path("search/", views.search, name="search"),
    path("free/", views.free_places, name="free"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:attraction_id>/", views.attraction_detail, name="detail"),
]
