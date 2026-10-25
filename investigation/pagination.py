"""Pagination de l'API, avec des clés de réponse en français."""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginationFrancaise(PageNumberPagination):
    """Pagination standard : 20 éléments, paramètre `taille_page`."""

    page_size = 20
    page_size_query_param = "taille_page"
    max_page_size = 100

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "total": self.page.paginator.count,
                "suivant": self.get_next_link(),
                "precedent": self.get_previous_link(),
                "resultats": data,
            }
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:
        return {
            "type": "object",
            "properties": {
                "total": {"type": "integer"},
                "suivant": {"type": "string", "nullable": True},
                "precedent": {"type": "string", "nullable": True},
                "resultats": schema,
            },
        }

    def get_schema_operation_parameters(self, view) -> list[dict]:
        """Documente les paramètres de pagination en français dans Swagger."""
        return [
            {
                "name": "page",
                "required": False,
                "in": "query",
                "description": "Numéro de page (commence à 1).",
                "schema": {"type": "integer", "minimum": 1},
            },
            {
                "name": "taille_page",
                "required": False,
                "in": "query",
                "description": (
                    "Nombre de résultats par page (1 à 100, 20 par défaut)."
                ),
                "schema": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": self.max_page_size,
                },
            },
        ]
