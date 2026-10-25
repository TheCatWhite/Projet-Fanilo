"""
Client WhatsApp — point d'extension futur.

WhatsApp ne permet pas l'accès aux conversations privées. Seule l'API
WhatsApp Business officielle, utilisée par une organisation disposant d'un
consentement, pourra être intégrée. Aucune donnée privée n'est collectée ici.
"""

from __future__ import annotations


class ClientWhatsApp:
    """Squelette d'intégration à l'API WhatsApp Business officielle."""

    def __init__(self, jeton_acces: str | None = None) -> None:
        self.jeton_acces = jeton_acces

    def analyser_message_public(self, identifiant_message: str) -> dict:
        raise NotImplementedError(
            "L'intégration WhatsApp n'est pas activée dans le MVP. "
            "Les captures et informations publiques doivent être saisies "
            "manuellement par le journaliste."
        )
