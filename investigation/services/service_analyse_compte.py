"""
Service d'analyse des comptes à l'origine des publications.

Approche par règles simples et explicables, sans jugement de véracité :
chaque alerte est un indice à vérifier manuellement par le journaliste.
"""

from __future__ import annotations

import re

from django.utils import timezone

from investigation.models import AlerteCompte, PublicationSource
from investigation.services.service_similarite import normaliser_texte

TYPES_AUTOMATIQUES = {
    AlerteCompte.TypeAlerte.COMPTE_RECENT,
    AlerteCompte.TypeAlerte.FAIBLE_ACTIVITE,
    AlerteCompte.TypeAlerte.NOM_IMPOSTEUR,
    AlerteCompte.TypeAlerte.PROFIL_ANONYME,
}

MOTS_CLES_NOM_SUSPECT = (
    "officiel",
    "officielle",
    "alerte",
    "info",
    "infos",
    "urgence",
    "urgent",
    "direct",
    "vraie",
    "verite",
)


def detecter_compte_recent(publication_source: PublicationSource) -> dict | None:
    """Signale un compte créé il y a moins de 30 jours."""
    date_creation = publication_source.date_creation_compte
    if date_creation is None:
        return None

    age_jours = (timezone.localdate() - date_creation).days
    if age_jours >= 30:
        return None

    age_affiche = max(0, age_jours)
    return {
        "type_alerte": AlerteCompte.TypeAlerte.COMPTE_RECENT,
        "gravite": AlerteCompte.Gravite.ELEVEE,
        "description": (
            f"Le compte a été créé il y a {age_affiche} jour(s), soit moins de "
            "30 jours avant l'analyse. Son historique est donc très limité."
        ),
    }


def detecter_faible_activite(publication_source: PublicationSource) -> dict | None:
    """Signale une audience inférieure à 100 abonnés."""
    nombre_abonnes = publication_source.nombre_abonnes
    if nombre_abonnes is None or nombre_abonnes >= 100:
        return None

    return {
        "type_alerte": AlerteCompte.TypeAlerte.FAIBLE_ACTIVITE,
        "gravite": AlerteCompte.Gravite.MOYENNE,
        "description": (
            f"Le compte ne compte que {nombre_abonnes} abonné(s), sous le seuil "
            "de 100. Sa portée habituelle est faible, ce qui peut indiquer un "
            "compte de circonstance ou un relais secondaire."
        ),
    }


def detecter_nom_suspect(publication_source: PublicationSource) -> dict | None:
    """
    Signale un nom évoquant une source officielle.

    La règle ne prouve pas une usurpation : elle invite à vérifier
    l'authenticité du compte auprès de l'institution concernée.
    """
    nom_normalise = normaliser_texte(publication_source.nom_auteur)
    if not nom_normalise:
        return None

    motif = r"\b(" + "|".join(
        re.escape(normaliser_texte(mot)) for mot in MOTS_CLES_NOM_SUSPECT
    ) + r")\b"
    correspondance = re.search(motif, nom_normalise)
    if not correspondance:
        return None

    terme = correspondance.group(1)
    return {
        "type_alerte": AlerteCompte.TypeAlerte.NOM_IMPOSTEUR,
        "gravite": AlerteCompte.Gravite.MOYENNE,
        "description": (
            f"Le nom du compte contient le terme « {terme} », évocateur d'une "
            "source officielle ou d'une urgence. L'authenticité du compte doit "
            "être vérifiée manuellement."
        ),
    }


def detecter_profil_anonyme(publication_source: PublicationSource) -> dict | None:
    """Signale un profil sans URL, sans date de création ni audience."""
    if (
        not publication_source.url_profil_auteur
        and publication_source.date_creation_compte is None
        and publication_source.nombre_abonnes is None
    ):
        return {
            "type_alerte": AlerteCompte.TypeAlerte.PROFIL_ANONYME,
            "gravite": AlerteCompte.Gravite.MOYENNE,
            "description": (
                "Aucune URL de profil, date de création ni audience n'est "
                "renseignée. Le compte est difficile à identifier et à recouper."
            ),
        }
    return None


def _detecter_toutes(publication_source: PublicationSource) -> list[dict]:
    """Exécute tous les détecteurs de compte et retourne les alertes brutes."""
    detections = [
        detecter_compte_recent(publication_source),
        detecter_faible_activite(publication_source),
        detecter_nom_suspect(publication_source),
        detecter_profil_anonyme(publication_source),
    ]
    return [detection for detection in detections if detection is not None]


def _persister_alertes(
    publication_source: PublicationSource,
    detections: list[dict],
) -> list[AlerteCompte]:
    """Remplace les alertes automatiques puis enregistre les nouvelles."""
    # Les alertes de type « autre » (ajout manuel) sont préservées.
    publication_source.alertes_compte.filter(
        type_alerte__in=TYPES_AUTOMATIQUES
    ).delete()

    alertes = [
        AlerteCompte(
            publication_source=publication_source,
            type_alerte=detection["type_alerte"],
            gravite=detection["gravite"],
            description=detection["description"],
        )
        for detection in detections
    ]
    if alertes:
        AlerteCompte.objects.bulk_create(alertes)

    # Relecture pour garantir des identifiants exploitables par l'API.
    return list(
        publication_source.alertes_compte.filter(
            type_alerte__in=TYPES_AUTOMATIQUES
        ).order_by("id")
    )


def generer_alertes_compte(publication_source: PublicationSource) -> list[AlerteCompte]:
    """Détecte puis enregistre les alertes d'un compte."""
    return _persister_alertes(publication_source, _detecter_toutes(publication_source))


def analyser_compte(publication_source: PublicationSource) -> list[AlerteCompte]:
    """
    Analyse complète d'un compte.

    La gravité du nom suspect est relevée lorsque le compte est également
    récent ou anonyme. Les alertes sont idempotentes : un nouvel appel remplace
    les alertes automatiques précédentes.
    """
    detections = _detecter_toutes(publication_source)
    types_detectes = {detection["type_alerte"] for detection in detections}

    if AlerteCompte.TypeAlerte.NOM_IMPOSTEUR in types_detectes and (
        AlerteCompte.TypeAlerte.COMPTE_RECENT in types_detectes
        or AlerteCompte.TypeAlerte.PROFIL_ANONYME in types_detectes
    ):
        for detection in detections:
            if detection["type_alerte"] == AlerteCompte.TypeAlerte.NOM_IMPOSTEUR:
                detection["gravite"] = AlerteCompte.Gravite.ELEVEE
                detection["description"] += (
                    " Le cumul avec un compte récent ou anonyme renforce le "
                    "besoin de vérification."
                )

    return _persister_alertes(publication_source, detections)
