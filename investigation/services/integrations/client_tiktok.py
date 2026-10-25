"""
Client TikTok — point d'extension futur.

L'intégration devra passer par une API officielle et se limiter aux contenus
publics. Le MVP ne réalise aucun scraping.
"""

from __future__ import annotations


class ClientTikTok:
    """Squelette d'intégration à l'API officielle TikTok."""

    def __init__(self, jeton_acces: str | None = None) -> None:
        self.jeton_acces = jeton_acces

    def rechercher_videos_publiques(self, requete: str) -> list[dict]:
        raise NotImplementedError(
            "L'intégration TikTok n'est pas activée dans le MVP. "
            "La saisie manuelle des publications publiques est requise."
        )
