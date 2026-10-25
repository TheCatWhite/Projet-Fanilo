"""
Service de propagation.

Reconstitue la chronologie des publications, détecte la première occurrence
publique (« source zéro ») et construit un arbre exploitable par l'interface
React. Aucune donnée privée n'est collectée : seules les saisies manuelles du
journaliste sont utilisées.
"""

from __future__ import annotations

from collections import Counter

from investigation.models import AlerteCompte, LienPropagation, PublicationSource
from investigation.services.service_similarite import (
    SEUIL_LIEN_PROPAGATION,
    calculer_similarite,
)

# Libellés lisibles des indicateurs de risque affichés dans le graphe.
ETIQUETTES_RISQUE = {
    AlerteCompte.TypeAlerte.COMPTE_RECENT: "Compte récent",
    AlerteCompte.TypeAlerte.FAIBLE_ACTIVITE: "Faible audience",
    AlerteCompte.TypeAlerte.NOM_IMPOSTEUR: "Nom potentiellement trompeur",
    AlerteCompte.TypeAlerte.PROFIL_ANONYME: "Profil anonyme",
    AlerteCompte.TypeAlerte.COMPORTEMENT_SUSPECT: "Comportement suspect",
    AlerteCompte.TypeAlerte.AUTRE: "Autre signal",
}


def detecter_premiere_publication(rumeur) -> PublicationSource | None:
    """
    Identifie la publication la plus ancienne et met à jour les indicateurs.

    En cas d'égalité de date, l'identifiant le plus faible départage.
    Retourne la publication détectée ou None si la rumeur n'a aucune publication.
    """
    publications = list(
        rumeur.publications.order_by("date_publication", "id").only(
            "id",
            "date_publication",
            "est_premiere_detection",
        )
    )
    if not publications:
        return None

    premiere = publications[0]
    a_modifier: list[PublicationSource] = []
    for publication in publications:
        doit_etre_premiere = publication.pk == premiere.pk
        if publication.est_premiere_detection != doit_etre_premiere:
            publication.est_premiere_detection = doit_etre_premiere
            a_modifier.append(publication)

    if a_modifier:
        PublicationSource.objects.bulk_update(a_modifier, ["est_premiere_detection"])

    premiere.est_premiere_detection = True
    return premiere


def creer_liens_propagation(publication_source: PublicationSource) -> list[LienPropagation]:
    """
    Compare une publication aux autres publications de la même rumeur.

    Un lien est créé lorsque la similarité atteint 0,80. Le sens du lien suit
    la chronologie : la publication la plus ancienne devient le parent. Une
    publication enfant ne possède qu'un seul parent ; si un meilleur parent est
    trouvé, le lien existant est mis à jour.
    """
    if not publication_source.texte_brut.strip():
        return []

    rumeur = publication_source.rumeur
    autres_publications = list(
        rumeur.publications.exclude(pk=publication_source.pk)
        .exclude(texte_brut="")
        .only("id", "date_publication", "texte_brut")
    )

    correspondances: list[tuple[float, PublicationSource]] = []
    for autre in autres_publications:
        score = calculer_similarite(publication_source.texte_brut, autre.texte_brut)
        if score >= SEUIL_LIEN_PROPAGATION:
            correspondances.append((score, autre))

    # Les meilleurs scores sont traités en premier.
    correspondances.sort(key=lambda element: -element[0])

    liens_touches: list[LienPropagation] = []
    for score, autre in correspondances:
        date_source = publication_source.date_publication
        date_autre = autre.date_publication
        if (date_autre, autre.id) < (date_source, publication_source.id):
            parent, enfant = autre, publication_source
        else:
            parent, enfant = publication_source, autre

        lien_existant = LienPropagation.objects.filter(
            publication_enfant=enfant
        ).first()

        if lien_existant:
            # On ne remplace le parent que si la nouvelle correspondance est meilleure.
            if score > lien_existant.score_similarite:
                lien_existant.publication_parent = parent
                lien_existant.score_similarite = score
                lien_existant.save(
                    update_fields=["publication_parent", "score_similarite"]
                )
                liens_touches.append(lien_existant)
            continue

        lien = LienPropagation.objects.create(
            rumeur=rumeur,
            publication_parent=parent,
            publication_enfant=enfant,
            score_similarite=score,
        )
        liens_touches.append(lien)

    return liens_touches


def _formater_nombre(valeur: float) -> str:
    """Formate un nombre avec la virgule décimale française."""
    return f"{valeur:.1f}".replace(".", ",")


def _pluriel(nombre: float, singulier: str, pluriel: str) -> str:
    return singulier if nombre <= 1 else pluriel


def calculer_statistiques_propagation(rumeur) -> dict:
    """Calcule les statistiques de diffusion d'une rumeur."""
    publications = list(
        rumeur.publications.order_by("date_publication", "id").only(
            "id",
            "plateforme",
            "date_publication",
        )
    )
    nombre_publications = len(publications)

    if not publications:
        return {
            "nombre_publications": 0,
            "plateformes": [],
            "premiere_publication": None,
            "derniere_publication": None,
            "vitesse_estimee": "Aucune publication enregistrée",
            "duree_heures": 0.0,
            "repartition_plateformes": {},
        }

    premiere = publications[0]
    derniere = publications[-1]
    plateformes = sorted({publication.plateforme for publication in publications})
    repartition = dict(
        Counter(publication.plateforme for publication in publications).most_common()
    )
    duree_secondes = max(
        0.0,
        (derniere.date_publication - premiere.date_publication).total_seconds(),
    )
    duree_heures = round(duree_secondes / 3600, 2)

    if nombre_publications == 1:
        vitesse = "1 publication enregistrée"
    elif duree_secondes <= 0:
        vitesse = f"{nombre_publications} publications enregistrées à la même date"
    elif duree_secondes < 3600:
        minutes = max(1, round(duree_secondes / 60))
        vitesse = (
            f"{nombre_publications} publications en {minutes} "
            f"{_pluriel(minutes, 'minute', 'minutes')}"
        )
    elif duree_secondes < 172800:
        heures = duree_secondes / 3600
        vitesse = (
            f"{nombre_publications} publications en {_formater_nombre(heures)} "
            f"{_pluriel(heures, 'heure', 'heures')}"
        )
    else:
        jours = duree_secondes / 86400
        vitesse = (
            f"{nombre_publications} publications en {_formater_nombre(jours)} "
            f"{_pluriel(jours, 'jour', 'jours')}"
        )

    return {
        "nombre_publications": nombre_publications,
        "plateformes": plateformes,
        "premiere_publication": premiere.date_publication.isoformat(),
        "derniere_publication": derniere.date_publication.isoformat(),
        "vitesse_estimee": vitesse,
        "duree_heures": duree_heures,
        "repartition_plateformes": repartition,
    }


def _indicateurs_risque(publication: PublicationSource) -> list[str]:
    """Transforme les alertes de compte en libellés synthétiques."""
    indicateurs: list[str] = []
    for alerte in publication.alertes_compte.all():
        libelle = ETIQUETTES_RISQUE.get(alerte.type_alerte, "Autre signal")
        if alerte.gravite == AlerteCompte.Gravite.ELEVEE:
            libelle = f"{libelle} (gravité élevée)"
        if libelle not in indicateurs:
            indicateurs.append(libelle)
    return indicateurs


def construire_arbre_propagation(rumeur) -> dict:
    """
    Construit la structure JSON destinée au composant React de propagation.

    Le résultat contient les nœuds, les liens orientés et les statistiques.
    """
    premiere = detecter_premiere_publication(rumeur)
    publications = list(
        rumeur.publications.prefetch_related("alertes_compte").order_by(
            "date_publication",
            "id",
        )
    )
    liens = rumeur.liens_propagation.select_related(
        "publication_parent",
        "publication_enfant",
    ).order_by("detecte_le", "id")

    noeuds = []
    for publication in publications:
        noeuds.append(
            {
                "id": publication.id,
                "plateforme": publication.plateforme,
                "plateforme_libelle": publication.get_plateforme_display(),
                "nom_auteur": publication.nom_auteur,
                "url_publication": publication.url_publication,
                "date_publication": publication.date_publication.isoformat(),
                "est_premiere_detection": publication.est_premiere_detection,
                "indicateurs_risque": _indicateurs_risque(publication),
                "nombre_alertes": len(
                    [alerte for alerte in publication.alertes_compte.all()]
                ),
            }
        )

    noeud_premiere = next(
        (
            noeud
            for noeud in noeuds
            if premiere is not None and noeud["id"] == premiere.id
        ),
        None,
    )

    liens_json = [
        {
            "publication_parent_id": lien.publication_parent_id,
            "publication_enfant_id": lien.publication_enfant_id,
            "score_similarite": lien.score_similarite,
        }
        for lien in liens
        if lien.publication_parent_id is not None
    ]

    return {
        "rumeur_id": rumeur.id,
        "premiere_publication_detectee": noeud_premiere,
        "noeuds": noeuds,
        "liens": liens_json,
        "statistiques_propagation": calculer_statistiques_propagation(rumeur),
    }
