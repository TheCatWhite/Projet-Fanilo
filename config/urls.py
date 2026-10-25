"""Routage principal : administration, API, documentation et médias en développement."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
]

# La documentation interactive peut être désactivée en production via
# DOCUMENTATION_ACTIVE=False dans .env.
if settings.DOCUMENTATION_ACTIVE:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

urlpatterns += [
    path("api/", include("investigation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "FactCheck Mada — Administration"
admin.site.site_title = "FactCheck Mada"
admin.site.index_title = "Gestion de l'investigation"
