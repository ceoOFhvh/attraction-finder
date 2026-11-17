from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("", include("web.homepage.urls")),
    path("attractions/", include("web.catalog.urls")),
    path("categories/", include("web.categories.urls")),
]
handler404 = "web.homepage.views.not_found"

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
