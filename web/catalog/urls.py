from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.attraction_list, name="list"),
    path("<int:attraction_id>/", views.attraction_detail, name="detail"),
]
