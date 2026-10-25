"""Permissions et helpers d'accès aux données."""

from rest_framework.permissions import BasePermission

from investigation.models import Rumeur


def est_administrateur(utilisateur) -> bool:
    """Indique si l'utilisateur peut consulter toutes les rédactions."""
    return bool(
        utilisateur
        and utilisateur.is_authenticated
        and getattr(utilisateur, "est_administrateur", False)
    )


class EstProprietaireRumeur(BasePermission):
    """Autorise l'accès aux rumeurs du journaliste ou à un administrateur."""

    message = "Vous n'avez pas accès à cette rumeur."

    def has_object_permission(self, request, view, obj) -> bool:
        if est_administrateur(request.user):
            return True
        if isinstance(obj, Rumeur):
            return obj.cree_par_id == request.user.id
        rumeur = getattr(obj, "rumeur", None)
        return bool(rumeur and rumeur.cree_par_id == request.user.id)
