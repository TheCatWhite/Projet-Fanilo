"""
Service d'analyse du texte des rumeurs.

Détection par expressions régulières et listes de mots-clés français et
malagasy. L'objectif est de produire des indices explicables (expressions
retrouvées, type de signal, gravité) et non un verdict de vérité.
"""

from __future__ import annotations

import re

from investigation.models import AlerteTexte, Rumeur
from investigation.services.service_similarite import normaliser_texte

# ---------------------------------------------------------------------------
# Lexiques (les recherches sont effectuées sur le texte normalisé)
# ---------------------------------------------------------------------------

EXPRESSIONS_ALARMISTES = [
    "urgence",
    "urgent",
    "danger",
    "dangereux",
    "dangereuse",
    "dangereuses",
    "alerte",
    "alarme",
    "catastrophe",
    "panique",
    "mort",
    "morts",
    "pénurie",
    "empoisonnement",
    "complot",
    "censure",
    "avant qu'ils suppriment",
    "avant qu'il soit trop tard",
    "vonjy",
    "loza",
    "maika",
    "haingana",
    "mampidi-doza",
    "fahafatesana",
    "mosary",
]

EXPRESSIONS_APPEL_PARTAGE = [
    "partagez",
    "partager",
    "transmettez",
    "transmettre",
    "envoyez à tous",
    "faites tourner",
    "diffusez",
    "copiez-collez",
    "ne gardez pas pour vous",
    "zarao",
    "mizara",
    "alefaso",
    "alefa",
    "aza tazonina",
    "ambarao",
]

EXPRESSIONS_SOURCE = [
    "ministère",
    "oms",
    "organisation mondiale de la santé",
    "unicef",
    "unesco",
    "police",
    "gendarmerie",
    "gouvernement",
    "préfecture",
    "tribunal",
    "douane",
    "hôpital",
    "médecin",
    "expert",
    "autorité",
    "communiqué",
    "journal officiel",
    "média officiel",
    "santé publique",
    "ministera",
    "polisy",
    "zandary",
    "mpitsabo",
    "hopitaly",
    "governemanta",
    "fanambarana",
    "tompon'andraikitra",
    "ofisialy",
]

EXPRESSIONS_FINANCIERES = [
    "argent",
    "gain",
    "cadeau",
    "remboursement",
    "prime",
    "allocation",
    "subvention",
    "gratuit",
    "gagner",
    "paiement",
    "virement",
    "mobile money",
    "mvola",
    "orange money",
    "airtel money",
    "ariary",
    "aide financière",
    "offert",
    "offerte",
    "vola",
    "fanomezana",
    "tambiny",
    "valisoa",
    "vola maimaim-poana",
]

EXPRESSIONS_URGENCE_ARTIFICIELLE = [
    "avant 24h",
    "avant 48h",
    "dans les prochaines heures",
    "dernière chance",
    "dernière minute",
    "aujourd'hui seulement",
    "immédiatement",
    "avant ce soir",
    "ne tardez pas",
    "vite",
]

EXPRESSIONS_SENSIBLES = [
    "viol",
    "meurtre",
    "assassinat",
    "cadavre",
    "sang",
    "émeute",
    "ethnie",
    "religion",
    "terrorisme",
    "drogue",
    "corruption",
    "élection",
    "enlèvement",
]

MOTS_CLES_AUTORISES = {
    AlerteTexte.TypeAlerte.LANGAGE_ALARMISTE,
    AlerteTexte.TypeAlerte.APPEL_AU_PARTAGE,
    AlerteTexte.TypeAlerte.ABSENCE_DE_SOURCE,
    AlerteTexte.TypeAlerte.PROMESSE_FINANCIERE,
    AlerteTexte.TypeAlerte.URGENCE_ARTIFICIELLE,
    AlerteTexte.TypeAlerte.CONTENU_SENSIBLE,
}

# Pondérations du score de risque texte (0-100).
PONDERATIONS = {
    AlerteTexte.TypeAlerte.LANGAGE_ALARMISTE: (8, 25),
    AlerteTexte.TypeAlerte.APPEL_AU_PARTAGE: (10, 20),
    AlerteTexte.TypeAlerte.ABSENCE_DE_SOURCE: (20, 20),
    AlerteTexte.TypeAlerte.PROMESSE_FINANCIERE: (10, 25),
    AlerteTexte.TypeAlerte.URGENCE_ARTIFICIELLE: (7, 15),
    AlerteTexte.TypeAlerte.CONTENU_SENSIBLE: (7, 20),
}


# ---------------------------------------------------------------------------
# Outils de recherche
# ---------------------------------------------------------------------------

def _normaliser_expression(expression: str) -> str:
    return normaliser_texte(expression)


def _chercher_expressions(texte_normalise: str, expressions: list[str]) -> list[str]:
    """
    Retourne les expressions présentes, sans doublon et dans l'ordre du texte.

    Les limites de mots évitent qu'« info » corresponde à « information ».
    """
    correspondances: dict[str, str] = {}
    for expression in expressions:
        expression_normalisee = _normaliser_expression(expression)
        if expression_normalisee and expression_normalisee not in correspondances:
            correspondances[expression_normalisee] = expression

    if not correspondances:
        return []

    alternatives = sorted(correspondances.keys(), key=len, reverse=True)
    motif = (
        r"(?<![a-z0-9])("
        + "|".join(re.escape(expression) for expression in alternatives)
        + r")(?![a-z0-9])"
    )

    trouvees: list[tuple[int, str]] = []
    vues: set[str] = set()
    for correspondance in re.finditer(motif, texte_normalise):
        normale = correspondance.group(1)
        if normale in vues:
            continue
        vues.add(normale)
        trouvees.append((correspondance.start(), correspondances[normale]))

    trouvees.sort(key=lambda element: element[0])
    return [expression for _, expression in trouvees]


def _detection(
    type_alerte: str,
    gravite: str,
    expression: str,
    explication: str,
) -> dict:
    return {
        "type_alerte": type_alerte,
        "gravite": gravite,
        "expression_detectee": expression[:255],
        "explication": explication,
    }


# ---------------------------------------------------------------------------
# Détecteurs publics
# ---------------------------------------------------------------------------

def detecter_langage_alarmiste(texte: str) -> list[dict]:
    """Repère les mots ou formules créant un sentiment d'urgence ou de peur."""
    expressions = _chercher_expressions(normaliser_texte(texte), EXPRESSIONS_ALARMISTES)
    gravite = (
        AlerteTexte.Gravite.ELEVEE
        if len(expressions) >= 2
        else AlerteTexte.Gravite.MOYENNE
    )
    return [
        _detection(
            AlerteTexte.TypeAlerte.LANGAGE_ALARMISTE,
            gravite,
            expression,
            (
                f"L'expression « {expression} » relève d'un registre alarmiste. "
                "Ce type de formulation peut accélérer la diffusion sans apporter "
                "de preuve supplémentaire."
            ),
        )
        for expression in expressions
    ]


def detecter_appel_au_partage(texte: str) -> list[dict]:
    """Repère les injonctions à relayer massivement le message."""
    expressions = _chercher_expressions(normaliser_texte(texte), EXPRESSIONS_APPEL_PARTAGE)
    return [
        _detection(
            AlerteTexte.TypeAlerte.APPEL_AU_PARTAGE,
            AlerteTexte.Gravite.MOYENNE,
            expression,
            (
                f"L'expression « {expression} » incite à relayer le message. "
                "Un appel au partage ne constitue pas une vérification de la source."
            ),
        )
        for expression in expressions
    ]


def detecter_absence_source(texte: str) -> list[dict]:
    """Signale l'absence de mention d'une institution ou d'une source vérifiable."""
    texte_normalise = normaliser_texte(texte)
    if len(texte_normalise) < 20:
        return []

    sources = _chercher_expressions(texte_normalise, EXPRESSIONS_SOURCE)
    if sources:
        return []

    return [
        _detection(
            AlerteTexte.TypeAlerte.ABSENCE_DE_SOURCE,
            AlerteTexte.Gravite.MOYENNE,
            "Aucune source identifiable",
            (
                "Le texte ne mentionne ni ministère, ni institution, ni expert, "
                "ni média officiel permettant de recouper l'information. "
                "Cette absence doit être comblée avant toute publication."
            ),
        )
    ]


def detecter_promesse_financiere(texte: str) -> list[dict]:
    """Repère les promesses de gain, de remboursement ou d'argent facile."""
    expressions = _chercher_expressions(
        normaliser_texte(texte),
        EXPRESSIONS_FINANCIERES,
    )
    return [
        _detection(
            AlerteTexte.TypeAlerte.PROMESSE_FINANCIERE,
            AlerteTexte.Gravite.ELEVEE,
            expression,
            (
                f"L'expression « {expression} » évoque un gain ou un avantage "
                "financier. Ce type de message est fréquemment utilisé pour des "
                "arnaques ; aucune donnée personnelle ne doit être transmise."
            ),
        )
        for expression in expressions
    ]


def detecter_urgence_artificielle(texte: str) -> list[dict]:
    """Repère les délais artificiels destinés à empêcher la vérification."""
    expressions = _chercher_expressions(
        normaliser_texte(texte),
        EXPRESSIONS_URGENCE_ARTIFICIELLE,
    )
    return [
        _detection(
            AlerteTexte.TypeAlerte.URGENCE_ARTIFICIELLE,
            AlerteTexte.Gravite.MOYENNE,
            expression,
            (
                f"L'expression « {expression} » impose un délai très court. "
                "L'urgence affichée peut empêcher le recoupement des faits."
            ),
        )
        for expression in expressions
    ]


def detecter_contenu_sensible(texte: str) -> list[dict]:
    """Signale les thèmes sensibles nécessitant une vigilance rédactionnelle."""
    expressions = _chercher_expressions(
        normaliser_texte(texte),
        EXPRESSIONS_SENSIBLES,
    )
    return [
        _detection(
            AlerteTexte.TypeAlerte.CONTENU_SENSIBLE,
            AlerteTexte.Gravite.ELEVEE,
            expression,
            (
                f"Le texte aborde un thème sensible (« {expression} »). "
                "Une vérification renforcée et une relecture éditoriale sont "
                "recommandées avant diffusion."
            ),
        )
        for expression in expressions
    ]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _detecter_toutes(texte: str) -> list[dict]:
    """Exécute l'ensemble des détecteurs de texte."""
    return [
        *detecter_langage_alarmiste(texte),
        *detecter_appel_au_partage(texte),
        *detecter_absence_source(texte),
        *detecter_promesse_financiere(texte),
        *detecter_urgence_artificielle(texte),
        *detecter_contenu_sensible(texte),
    ]


def _score_depuis_detections(detections: list[dict]) -> int:
    """Calcule le score de risque texte à partir des alertes détectées."""
    compteurs: dict[str, int] = {}
    for detection in detections:
        compteurs[detection["type_alerte"]] = (
            compteurs.get(detection["type_alerte"], 0) + 1
        )

    score = 0
    for type_alerte, nombre in compteurs.items():
        points, plafond = PONDERATIONS.get(type_alerte, (0, 0))
        score += min(plafond, points * nombre)
    return min(100, score)


def calculer_score_risque_texte(rumeur: Rumeur) -> int:
    """
    Retourne le score de risque texte de 0 à 100.

    Les alertes enregistrées sont utilisées en priorité. Si aucune analyse n'a
    encore été réalisée, le score est calculé à la volée sans persistance.
    """
    alertes = list(rumeur.alertes_texte.all())
    if alertes:
        detections = [
            {"type_alerte": alerte.type_alerte, "gravite": alerte.gravite}
            for alerte in alertes
        ]
    else:
        detections = _detecter_toutes(rumeur.contenu)
    return _score_depuis_detections(detections)


def analyser_texte(rumeur: Rumeur) -> dict:
    """
    Analyse le contenu d'une rumeur et remplace ses alertes automatiques.

    Retourne un dictionnaire contenant le score de risque et les alertes.
    Les alertes de type « autre » ajoutées manuellement sont conservées.
    """
    detections = _detecter_toutes(rumeur.contenu)

    rumeur.alertes_texte.filter(type_alerte__in=MOTS_CLES_AUTORISES).delete()
    alertes = [
        AlerteTexte(
            rumeur=rumeur,
            type_alerte=detection["type_alerte"],
            gravite=detection["gravite"],
            expression_detectee=detection["expression_detectee"],
            explication=detection["explication"],
        )
        for detection in detections
    ]
    if alertes:
        AlerteTexte.objects.bulk_create(alertes)

    # Relecture pour garantir des identifiants exploitables par l'API.
    alertes_enregistrees = list(
        rumeur.alertes_texte.filter(type_alerte__in=MOTS_CLES_AUTORISES).order_by(
            "id"
        )
    )

    return {
        "score_risque_texte": _score_depuis_detections(detections),
        "alertes": alertes_enregistrees,
        "nombre_alertes": len(alertes_enregistrees),
    }
