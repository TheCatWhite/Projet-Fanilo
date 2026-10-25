"""
Client Facebook — point d'extension futur.

Le MVP n'effectue aucune collecte automatique. Ce client devra utiliser
exclusivement une API officielle, avec un jeton d'accès fourni par le
journaliste ou la rédaction, et respecter les conditions d'utilisation.
"""

from __future__ import annotations


class ClientFacebook:
    """Squelette d'intégration à l'API officielle de Meta."""

    def __init__(self, jeton_acces: str | None = None) -> None:
        self.jeton_acces = jeton_acces

    def rechercher_publications_publiques(self, requete: str) -> list[dict]:
        raise NotImplementedError(
            "L'intégration Facebook n'est pas activée dans le MVP. "
            "La saisie manuelle des publications publiques est requise."
        )
