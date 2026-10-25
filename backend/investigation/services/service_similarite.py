"""
Service de similarité textuelle.

Méthode retenue pour le MVP : TF-IDF sur des n-grammes de caractères (3 et 4)
avec similarité cosinus, implémenté en Python pur. Ce choix évite une
dépendance lourde (scikit-learn) tout en restant robuste aux variantes
d'orthographe, aux accents et aux textes courts en français ou en malagasy.

Les seuils métier (0,90 pour un doublon de rumeur, 0,80 pour un lien de
propagation) sont appliqués par les vues et les services appelants.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from hashlib import sha256

LONGUEURS_NGRAMMES = (3, 4)
SEUIL_DOUBLON_RUMEUR = 0.90
SEUIL_LIEN_PROPAGATION = 0.80


def normaliser_texte(texte: str | None) -> str:
    """
    Normalise un texte pour la comparaison et l'empreinte.

    Étapes : décomposition Unicode, suppression des accents, minuscules,
    remplacement des ligatures, suppression des emojis/ponctuations, puis
    compactage des espaces.
    """
    if texte is None:
        return ""

    texte = str(texte).replace("œ", "oe").replace("Œ", "OE")
    texte = texte.replace("æ", "ae").replace("Æ", "AE")
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(caractere for caractere in texte if not unicodedata.combining(caractere))
    texte = texte.lower()
    # On ne conserve que les lettres latines, les chiffres et les espaces.
    texte = re.sub(r"[^a-z0-9\s]", " ", texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte


def calculer_empreinte(texte: str | None) -> str:
    """Retourne l'empreinte SHA-256 du texte normalisé."""
    return sha256(normaliser_texte(texte).encode("utf-8")).hexdigest()


def _extraire_ngrammes(texte_normalise: str) -> Counter[str]:
    """Compte les n-grammes de caractères d'un texte déjà normalisé."""
    compteur: Counter[str] = Counter()
    texte_padding = f" {texte_normalise} "
    for longueur in LONGUEURS_NGRAMMES:
        for debut in range(max(1, len(texte_padding) - longueur + 1)):
            gramme = texte_padding[debut : debut + longueur]
            if gramme.strip():
                compteur[gramme] += 1
    return compteur


def _vecteurs_tfidf(documents: Iterable[str]) -> list[dict[str, float]]:
    """Calcule des vecteurs TF-IDF normalisés pour un petit corpus."""
    jeux_ngrammes = [_extraire_ngrammes(document) for document in documents]
    nombre_documents = len(jeux_ngrammes)
    frequences_documentaires: Counter[str] = Counter()
    for jeu in jeux_ngrammes:
        frequences_documentaires.update(jeu.keys())

    vecteurs: list[dict[str, float]] = []
    for jeu in jeux_ngrammes:
        vecteur: dict[str, float] = {}
        for terme, frequence in jeu.items():
            idf = math.log(
                (1 + nombre_documents) / (1 + frequences_documentaires[terme])
            ) + 1
            vecteur[terme] = (1 + math.log(frequence)) * idf

        norme = math.sqrt(sum(valeur * valeur for valeur in vecteur.values()))
        if norme:
            vecteur = {terme: valeur / norme for terme, valeur in vecteur.items()}
        vecteurs.append(vecteur)
    return vecteurs


def _cosinus(vecteur_a: dict[str, float], vecteur_b: dict[str, float]) -> float:
    """Similarité cosinus entre deux vecteurs creux déjà normalisés."""
    if not vecteur_a or not vecteur_b:
        return 0.0
    # On parcourt le plus petit vecteur pour limiter les opérations.
    petit, grand = (vecteur_a, vecteur_b)
    if len(vecteur_b) < len(vecteur_a):
        petit, grand = vecteur_b, vecteur_a
    return sum(valeur * grand.get(terme, 0.0) for terme, valeur in petit.items())


def _recouvrement_ngrammes(texte_a: str, texte_b: str) -> float:
    """
    Calcule le recouvrement des n-grammes par rapport au texte le plus court.

    Cette mesure complète le cosinus : elle reste élevée lorsqu'une version
    raccourcie d'un message reprend l'essentiel du texte d'origine, ce qui est
    fréquent lors d'un relais sur WhatsApp ou TikTok.
    """
    grammes_a = set(_extraire_ngrammes(texte_a))
    grammes_b = set(_extraire_ngrammes(texte_b))
    if not grammes_a or not grammes_b:
        return 0.0
    return len(grammes_a & grammes_b) / min(len(grammes_a), len(grammes_b))


def calculer_similarite(texte1: str | None, texte2: str | None) -> float:
    """
    Calcule un score de similarité entre 0 et 1.

    Le score combine à parts égales :
    - la similarité cosinus de vecteurs TF-IDF (n-grammes de caractères) ;
    - le recouvrement des n-grammes du texte le plus court.

    Ce compromis détecte aussi bien les copier-coller que les versions
    raccourcies ou légèrement réécrites. Le score vaut 1,0 pour deux textes
    identiques après normalisation et 0,0 si l'un des textes est vide.
    """
    texte1_normalise = normaliser_texte(texte1)
    texte2_normalise = normaliser_texte(texte2)

    if not texte1_normalise or not texte2_normalise:
        return 0.0
    if texte1_normalise == texte2_normalise:
        return 1.0

    vecteur1, vecteur2 = _vecteurs_tfidf([texte1_normalise, texte2_normalise])
    cosinus = _cosinus(vecteur1, vecteur2)
    recouvrement = _recouvrement_ngrammes(texte1_normalise, texte2_normalise)
    score = 0.5 * cosinus + 0.5 * recouvrement
    return round(max(0.0, min(1.0, score)), 4)


def rechercher_rumeurs_similaires(
    texte: str | None,
    queryset=None,
    seuil: float = 0.0,
    exclure_id: int | None = None,
    limite: int | None = None,
) -> list[dict]:
    """
    Recherche les rumeurs proches d'un texte.

    Retourne une liste triée par score décroissant :
    [{"id", "titre", "score_similarite", "cree_le", "statut"}, ...].

    Le queryset doit être restreint au périmètre autorisé de l'utilisateur
    (les vues transmettent les rumeurs du journaliste connecté).
    """
    # Import tardif pour éviter un cycle modèles → services → modèles.
    from investigation.models import Rumeur

    if not normaliser_texte(texte):
        return []

    if queryset is None:
        queryset = Rumeur.objects.all()

    if exclure_id is not None:
        queryset = queryset.exclude(pk=exclure_id)

    resultats: list[dict] = []
    candidates = queryset.only("id", "titre", "contenu", "cree_le", "statut")
    for rumeur in candidates.iterator():
        score = calculer_similarite(texte, rumeur.contenu)
        if score >= seuil:
            resultats.append(
                {
                    "id": rumeur.id,
                    "titre": rumeur.titre,
                    "score_similarite": score,
                    "cree_le": rumeur.cree_le,
                    "statut": rumeur.statut,
                }
            )

    resultats.sort(key=lambda element: (-element["score_similarite"], element["id"]))
    if limite is not None:
        resultats = resultats[:limite]
    return resultats


def rechercher_doublon_exact(
    empreinte: str,
    queryset=None,
    exclure_id: int | None = None,
):
    """Retourne la première rumeur dont l'empreinte SHA-256 est identique."""
    from investigation.models import Rumeur

    if queryset is None:
        queryset = Rumeur.objects.all()
    if exclure_id is not None:
        queryset = queryset.exclude(pk=exclure_id)
    return queryset.filter(empreinte_contenu=empreinte).first()
