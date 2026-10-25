"""
Gestionnaire d'exceptions de l'API.

DRF et SimpleJWT fournissent déjà des traductions françaises. Ce gestionnaire
complète la traduction des messages les plus fréquents et uniformise les
erreurs 404 afin que l'interface React affiche toujours un texte français.
"""

from __future__ import annotations

from rest_framework.views import exception_handler

TRADUCTIONS = {
    "Authentication credentials were not provided.": (
        "Identifiants d'authentification non fournis."
    ),
    "You do not have permission to perform this action.": (
        "Vous n'avez pas la permission d'effectuer cette action."
    ),
    "Not found.": "Ressource introuvable.",
    "Invalid token.": "Jeton invalide.",
    "Token is invalid or expired": "Jeton invalide ou expiré.",
    "Given token not valid for any token type": "Jeton invalide ou expiré.",
    "Token is invalid": "Le jeton est invalide.",
    "Token is expired": "Le jeton est expiré.",
    "Token has no type": "Le jeton ne possède pas de type.",
    "Token has wrong type": "Le type du jeton est incorrect.",
    "No active account found with the given credentials": (
        "Identifiants invalides."
    ),
    "This field is required.": "Ce champ est obligatoire.",
    "This field may not be blank.": "Ce champ ne peut pas être vide.",
    "This field may not be null.": "Ce champ ne peut pas être nul.",
    "Enter a valid URL.": "Saisissez une URL valide.",
    "Enter a valid email address.": "Saisissez une adresse e-mail valide.",
}


def _traduire(valeur):
    """Traduit récursivement les messages connus."""
    if isinstance(valeur, str):
        if valeur in TRADUCTIONS:
            return TRADUCTIONS[valeur]
        if valeur.startswith("No ") and "matches the given query" in valeur:
            return "Ressource introuvable."
        return valeur
    if isinstance(valeur, list):
        return [_traduire(element) for element in valeur]
    if isinstance(valeur, dict):
        return {cle: _traduire(element) for cle, element in valeur.items()}
    return valeur


def gestionnaire_exceptions_francais(exc, context):
    """Traduit la réponse d'erreur standard de DRF."""
    response = exception_handler(exc, context)
    if response is not None:
        response.data = _traduire(response.data)
    return response
