"""Routage principal : administration, API et médias en développement."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("investigation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "FactCheck Mada — Administration"
admin.site.site_title = "FactCheck Mada"
admin.site.index_title = "Gestion de l'investigation"
