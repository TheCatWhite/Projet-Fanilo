"""
Service de génération des rapports de vérification.

Le rapport rassemble des indices (source zéro, chronologie, alertes) et produit
un score de crédibilité ainsi qu'un niveau de risque. Il ne conclut jamais à la
véracité ou à la fausseté d'une information : la décision reste humaine.
"""

from __future__ import annotations

import os
from html import escape
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils import timezone

from investigation.models import (
    AlerteCompte,
    AlerteTexte,
    RapportVerification,
    Rumeur,
)
from investigation.services.service_analyse_compte import analyser_compte
from investigation.services.service_analyse_texte import analyser_texte
from investigation.services.service_propagation import (
    calculer_statistiques_propagation,
    detecter_premiere_publication,
)

AVERTISSEMENT = (
    "Ces éléments sont des indices destinés à orienter les vérifications. "
    "Ils ne constituent pas une conclusion sur la véracité de l'information. "
    "La décision éditoriale appartient au journaliste."
)

PENALITES_GRAVITE_TEXTE = {
    AlerteTexte.Gravite.ELEVEE: 12,
    AlerteTexte.Gravite.MOYENNE: 7,
    AlerteTexte.Gravite.FAIBLE: 3,
}

PENALITES_GRAVITE_COMPTE = {
    AlerteCompte.Gravite.ELEVEE: 10,
    AlerteCompte.Gravite.MOYENNE: 5,
    AlerteCompte.Gravite.FAIBLE: 2,
}


# ---------------------------------------------------------------------------
# Collecte
# ---------------------------------------------------------------------------

def formater_date(valeur) -> str:
    """Formate une date en français, dans le fuseau de Madagascar."""
    if valeur is None:
        return "Non renseignée"
    if hasattr(valeur, "hour"):
        valeur = timezone.localtime(valeur)
        return valeur.strftime("%d/%m/%Y à %H:%M")
    return valeur.strftime("%d/%m/%Y")


def collecter_donnees_rapport(rumeur: Rumeur) -> dict:
    """Rassemble toutes les données nécessaires au rapport."""
    premiere = detecter_premiere_publication(rumeur)
    publications = list(
        rumeur.publications.prefetch_related("alertes_compte").order_by(
            "date_publication",
            "id",
        )
    )
    alertes_compte = list(
        AlerteCompte.objects.filter(publication_source__rumeur=rumeur)
        .select_related("publication_source")
        .order_by("-cree_le", "id")
    )
    alertes_texte = list(rumeur.alertes_texte.all().order_by("-cree_le", "id"))
    statistiques = calculer_statistiques_propagation(rumeur)

    return {
        "rumeur": {
            "id": rumeur.id,
            "titre": rumeur.titre,
            "contenu": rumeur.contenu,
            "langue": rumeur.langue,
            "statut": rumeur.statut,
            "cree_le": rumeur.cree_le,
            "journaliste": rumeur.cree_par.username,
            "redaction": rumeur.cree_par.redaction,
        },
        "premiere_publication": (
            {
                "id": premiere.id,
                "plateforme": premiere.plateforme,
                "plateforme_libelle": premiere.get_plateforme_display(),
                "nom_auteur": premiere.nom_auteur,
                "url_publication": premiere.url_publication,
                "date_publication": premiere.date_publication,
                "date_publication_lisible": formater_date(premiere.date_publication),
                "nombre_abonnes": premiere.nombre_abonnes,
            }
            if premiere
            else None
        ),
        "publications": [
            {
                "id": publication.id,
                "plateforme": publication.plateforme,
                "plateforme_libelle": publication.get_plateforme_display(),
                "nom_auteur": publication.nom_auteur,
                "date_publication": publication.date_publication,
                "date_publication_lisible": formater_date(publication.date_publication),
                "est_premiere_detection": publication.est_premiere_detection,
            }
            for publication in publications
        ],
        "alertes_compte": [
            {
                "id": alerte.id,
                "publication_id": alerte.publication_source_id,
                "type_alerte": alerte.type_alerte,
                "type_libelle": alerte.get_type_alerte_display(),
                "gravite": alerte.gravite,
                "gravite_libelle": alerte.get_gravite_display(),
                "description": alerte.description,
            }
            for alerte in alertes_compte
        ],
        "alertes_texte": [
            {
                "id": alerte.id,
                "type_alerte": alerte.type_alerte,
                "type_libelle": alerte.get_type_alerte_display(),
                "gravite": alerte.gravite,
                "gravite_libelle": alerte.get_gravite_display(),
                "expression_detectee": alerte.expression_detectee,
                "explication": alerte.explication,
            }
            for alerte in alertes_texte
        ],
        "liens": [
            {
                "publication_parent_id": lien.publication_parent_id,
                "publication_enfant_id": lien.publication_enfant_id,
                "score_similarite": lien.score_similarite,
            }
            for lien in rumeur.liens_propagation.all()
        ],
        "statistiques": statistiques,
    }


# ---------------------------------------------------------------------------
# Calculs
# ---------------------------------------------------------------------------

def calculer_score_credibilite(rumeur: Rumeur) -> int:
    """
    Calcule un indice de crédibilité de 0 à 100.

    Plus les signaux d'alerte sont nombreux et graves, plus le score baisse.
    La formule est volontairement simple, documentée et vérifiable.
    """
    alertes_texte = list(rumeur.alertes_texte.all())
    alertes_compte = list(
        AlerteCompte.objects.filter(publication_source__rumeur=rumeur)
    )
    publications = list(rumeur.publications.all())

    score = 100

    penalite_texte = sum(
        PENALITES_GRAVITE_TEXTE.get(alerte.gravite, 0) for alerte in alertes_texte
    )
    score -= min(45, penalite_texte)

    penalite_compte = sum(
        PENALITES_GRAVITE_COMPTE.get(alerte.gravite, 0) for alerte in alertes_compte
    )
    score -= min(30, penalite_compte)

    if any(
        alerte.type_alerte == AlerteTexte.TypeAlerte.ABSENCE_DE_SOURCE
        for alerte in alertes_texte
    ):
        score -= 8

    if not publications:
        score -= 15
    else:
        premiere = min(
            publications,
            key=lambda publication: (publication.date_publication, publication.id),
        )
        if premiere.date_creation_compte is not None:
            age_compte = (
                premiere.date_publication.date() - premiere.date_creation_compte
            ).days
            if age_compte < 30:
                score -= 5

        statistiques = calculer_statistiques_propagation(rumeur)
        if (
            statistiques["nombre_publications"] >= 5
            and 0 < statistiques["duree_heures"] <= 24
        ):
            score -= 5

    return max(0, min(100, int(score)))


def determiner_niveau_risque(score: int) -> str:
    """Convertit un score de crédibilité en niveau de risque éditorial."""
    if 80 <= score <= 100:
        return RapportVerification.NiveauRisque.FAIBLE
    if 60 <= score <= 79:
        return RapportVerification.NiveauRisque.MOYEN
    if 40 <= score <= 59:
        return RapportVerification.NiveauRisque.ELEVE
    return RapportVerification.NiveauRisque.TRES_ELEVE


def generer_resume(rumeur: Rumeur) -> str:
    """Produit un résumé neutre, factuel et journalistique."""
    donnees = collecter_donnees_rapport(rumeur)
    premiere = donnees["premiere_publication"]
    statistiques = donnees["statistiques"]
    nombre_alertes_compte = len(donnees["alertes_compte"])
    nombre_alertes_texte = len(donnees["alertes_texte"])
    score = calculer_score_credibilite(rumeur)
    niveau = determiner_niveau_risque(score)

    if not premiere:
        return (
            f"La rumeur « {rumeur.titre} » est enregistrée mais aucune publication "
            "source n'a encore été saisie. Aucune chronologie de diffusion ne peut "
            "donc être établie à ce stade. "
            f"Le score de crédibilité provisoire est de {score}/100 "
            f"(niveau de risque : {RapportVerification.NiveauRisque(niveau).label.lower()}). "
            f"{AVERTISSEMENT}"
        )

    plateformes = ", ".join(statistiques["plateformes"]) or "plateforme non précisée"
    nombre_publications = statistiques["nombre_publications"]
    publications = donnees["publications"]
    date_debut = publications[0]["date_publication_lisible"]
    date_fin = publications[-1]["date_publication_lisible"]
    return (
        f"La rumeur « {rumeur.titre} » a été détectée pour la première fois le "
        f"{premiere['date_publication_lisible']} sur "
        f"{premiere['plateforme_libelle']}, via le compte "
        f"« {premiere['nom_auteur']} ». "
        f"{nombre_publications} publication(s) ont été recensées entre le "
        f"{date_debut} et le {date_fin}, sur : "
        f"{plateformes}. "
        f"L'analyse automatique relève {nombre_alertes_compte} alerte(s) de compte "
        f"et {nombre_alertes_texte} alerte(s) de texte. "
        f"Le score de crédibilité s'établit à {score}/100, soit un niveau de risque "
        f"{RapportVerification.NiveauRisque(niveau).label.lower()}. "
        f"{AVERTISSEMENT}"
    )


def generer_recommandations(rumeur: Rumeur) -> list[str]:
    """Génère des recommandations éditoriales, sans verdict de vérité."""
    types_compte = set(
        AlerteCompte.objects.filter(
            publication_source__rumeur=rumeur
        ).values_list("type_alerte", flat=True)
    )
    types_texte = set(
        rumeur.alertes_texte.values_list("type_alerte", flat=True)
    )
    nombre_publications = rumeur.publications.count()
    plateformes = set(
        rumeur.publications.values_list("plateforme", flat=True)
    )

    recommandations = [
        "Contacter la source originale.",
        "Vérifier auprès de l'institution mentionnée.",
        "Rechercher des publications antérieures similaires.",
        "Ne pas publier sans confirmation officielle.",
    ]

    if AlerteCompte.TypeAlerte.COMPTE_RECENT in types_compte:
        recommandations.append(
            "Vérifier l'ancienneté et l'identité du compte à l'origine de la publication."
        )
    if AlerteCompte.TypeAlerte.NOM_IMPOSTEUR in types_compte:
        recommandations.append(
            "Confirmer l'authenticité du compte auprès de la plateforme ou de "
            "l'institution concernée."
        )
    if AlerteTexte.TypeAlerte.ABSENCE_DE_SOURCE in types_texte:
        recommandations.append(
            "Exiger une source nominative ou un document officiel avant toute reprise."
        )
    if AlerteTexte.TypeAlerte.PROMESSE_FINANCIERE in types_texte:
        recommandations.append(
            "Ne transmettre aucune donnée personnelle et n'effectuer aucun paiement."
        )
    if nombre_publications == 0:
        recommandations.append(
            "Ajouter les publications observées pour documenter la propagation."
        )
    if len(plateformes) >= 2:
        recommandations.append(
            "Comparer les versions diffusées sur chaque plateforme pour repérer "
            "les modifications du texte."
        )
    recommandations.append(
        "Conserver les URLs, captures d'écran et dates de collecte."
    )

    # Dédoublonnage tout en préservant l'ordre.
    return list(dict.fromkeys(recommandations))


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def generer_rapport(rumeur: Rumeur) -> RapportVerification:
    """
    Analyse la rumeur puis crée ou met à jour son rapport de vérification.

    L'analyse du texte et des comptes est relancée pour garantir un rapport
    complet et cohérent, même si le journaliste n'a pas appelé les endpoints
    d'analyse séparément.
    """
    analyser_texte(rumeur)
    for publication in rumeur.publications.all():
        analyser_compte(publication)

    score = calculer_score_credibilite(rumeur)
    niveau = determiner_niveau_risque(score)

    rapport, _ = RapportVerification.objects.update_or_create(
        rumeur=rumeur,
        defaults={
            "score_credibilite": score,
            "niveau_risque": niveau,
            "resume": generer_resume(rumeur),
            "recommandations": generer_recommandations(rumeur),
        },
    )
    return rapport


# ---------------------------------------------------------------------------
# Export PDF
# ---------------------------------------------------------------------------

def _enregistrer_fichier(champ, nom_fichier: str, contenu: bytes) -> None:
    """Remplace un fichier existant puis enregistre le nouveau contenu."""
    if champ:
        try:
            champ.delete(save=False)
        except OSError:
            pass
    champ.save(nom_fichier, ContentFile(contenu), save=True)


def generer_pdf_rapport(rumeur: Rumeur) -> RapportVerification:
    """Génère le PDF du rapport avec ReportLab et le stocke sur le rapport."""
    # Import local : permet de renvoyer une erreur claire si ReportLab manque.
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    rapport = getattr(rumeur, "rapport", None)
    if rapport is None:
        rapport = generer_rapport(rumeur)

    donnees = collecter_donnees_rapport(rumeur)
    premiere = donnees["premiere_publication"]

    # Police avec support complet des accents ; repli sur Helvetica.
    police_normale = "Helvetica"
    police_gras = "Helvetica-Bold"
    for chemin in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(chemin):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", chemin))
                chemin_gras = chemin.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
                if os.path.exists(chemin_gras):
                    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", chemin_gras))
                    police_gras = "DejaVuSans-Bold"
                else:
                    police_gras = "DejaVuSans"
                police_normale = "DejaVuSans"
                break
            except Exception:
                police_normale = "Helvetica"
                police_gras = "Helvetica-Bold"
                break

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Rapport de vérification — {rumeur.titre}",
        author="FactCheck Mada",
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        "TitreRapport",
        parent=styles["Title"],
        fontName=police_gras,
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#0f172a"),
    )
    style_sous_titre = ParagraphStyle(
        "SousTitreRapport",
        parent=styles["Normal"],
        fontName=police_normale,
        fontSize=9,
        textColor=colors.HexColor("#475569"),
    )
    style_section = ParagraphStyle(
        "SectionRapport",
        parent=styles["Heading2"],
        fontName=police_gras,
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#0e7490"),
    )
    style_texte = ParagraphStyle(
        "TexteRapport",
        parent=styles["Normal"],
        fontName=police_normale,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
    )
    style_petit = ParagraphStyle(
        "PetitRapport",
        parent=style_texte,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )
    style_avertissement = ParagraphStyle(
        "Avertissement",
        parent=style_texte,
        fontName=police_gras,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#9a3412"),
        alignment=TA_CENTER,
    )

    contenu = [
        Paragraph("FactCheck Mada", style_sous_titre),
        Paragraph("Rapport de vérification", style_titre),
        Paragraph(escape(rumeur.titre), style_section),
        Paragraph(
            f"Journaliste : {escape(rumeur.cree_par.username)} — "
            f"Rédaction : {escape(rumeur.cree_par.redaction or 'non renseignée')}",
            style_sous_titre,
        ),
        Spacer(1, 4 * mm),
    ]

    tableau_synthese = Table(
        [
            ["Score de crédibilité", "Niveau de risque", "Publications"],
            [
                f"{rapport.score_credibilite}/100",
                rapport.get_niveau_risque_display(),
                str(donnees["statistiques"]["nombre_publications"]),
            ],
        ],
        colWidths=[60 * mm, 60 * mm, 50 * mm],
    )
    tableau_synthese.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), police_gras),
                ("FONTNAME", (0, 1), (-1, 1), police_normale),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0c4a6e")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bae6fd")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    contenu.extend(
        [
            tableau_synthese,
            Paragraph("Résumé", style_section),
            Paragraph(escape(rapport.resume), style_texte),
        ]
    )

    contenu.append(Paragraph("Première publication détectée", style_section))
    if premiere:
        contenu.append(
            Paragraph(
                f"{escape(premiere['nom_auteur'])} — "
                f"{escape(premiere['plateforme_libelle'])} — "
                f"{escape(premiere['date_publication_lisible'])}",
                style_texte,
            )
        )
        if premiere["url_publication"]:
            contenu.append(
                Paragraph(escape(premiere["url_publication"]), style_petit)
            )
    else:
        contenu.append(
            Paragraph("Aucune publication source enregistrée.", style_texte)
        )

    contenu.append(Paragraph("Chronologie des publications", style_section))
    if donnees["publications"]:
        lignes = [["Date", "Plateforme", "Compte", "Première"]]
        for publication in donnees["publications"]:
            lignes.append(
                [
                    publication["date_publication_lisible"],
                    publication["plateforme_libelle"],
                    publication["nom_auteur"],
                    "Oui" if publication["est_premiere_detection"] else "Non",
                ]
            )
        tableau_chronologie = Table(
            lignes,
            colWidths=[38 * mm, 30 * mm, 70 * mm, 22 * mm],
            repeatRows=1,
        )
        tableau_chronologie.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), police_gras),
                    ("FONTNAME", (0, 1), (-1, -1), police_normale),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        contenu.append(tableau_chronologie)
    else:
        contenu.append(Paragraph("Aucune publication.", style_texte))

    contenu.append(Paragraph("Alertes de compte", style_section))
    if donnees["alertes_compte"]:
        for alerte in donnees["alertes_compte"]:
            contenu.append(
                Paragraph(
                    f"• <b>{escape(alerte['type_libelle'])}</b> "
                    f"({escape(alerte['gravite_libelle'])}) : "
                    f"{escape(alerte['description'])}",
                    style_texte,
                )
            )
    else:
        contenu.append(Paragraph("Aucune alerte de compte.", style_texte))

    contenu.append(Paragraph("Alertes de texte", style_section))
    if donnees["alertes_texte"]:
        for alerte in donnees["alertes_texte"]:
            contenu.append(
                Paragraph(
                    f"• <b>{escape(alerte['type_libelle'])}</b> "
                    f"({escape(alerte['gravite_libelle'])}) — "
                    f"« {escape(alerte['expression_detectee'])} » : "
                    f"{escape(alerte['explication'])}",
                    style_texte,
                )
            )
    else:
        contenu.append(Paragraph("Aucune alerte de texte.", style_texte))

    contenu.append(Paragraph("Recommandations", style_section))
    for recommandation in rapport.recommandations:
        contenu.append(Paragraph(f"• {escape(recommandation)}", style_texte))

    contenu.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph(escape(AVERTISSEMENT), style_avertissement),
            Paragraph(
                f"Rapport généré le {formater_date(rapport.genere_le)} — "
                "Analyse automatique, vérification humaine requise.",
                style_petit,
            ),
        ]
    )

    document.build(contenu)
    _enregistrer_fichier(
        rapport.fichier_pdf,
        f"rapport_{rumeur.id}.pdf",
        buffer.getvalue(),
    )
    return rapport


# ---------------------------------------------------------------------------
# Export image
# ---------------------------------------------------------------------------

def _charger_police(taille: int, gras: bool = False):
    """Charge une police DejaVu avec repli sur la police Pillow par défaut."""
    from PIL import ImageFont

    noms = (
        "DejaVuSans-Bold.ttf" if gras else "DejaVuSans.ttf",
        "DejaVuSans.ttf",
    )
    dossiers = (
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/dejavu",
        "/usr/share/fonts/TTF",
    )
    for dossier in dossiers:
        for nom in noms:
            chemin = os.path.join(dossier, nom)
            if os.path.exists(chemin):
                try:
                    return ImageFont.truetype(chemin, taille)
                except OSError:
                    continue
    try:
        return ImageFont.load_default(size=taille)
    except TypeError:  # Pillow ancien
        return ImageFont.load_default()


def _decouper_texte(dessin, texte: str, police, largeur_max: int) -> list[str]:
    """Découpe un texte en lignes tenant dans une largeur donnée."""
    mots = texte.split()
    lignes: list[str] = []
    ligne = ""
    for mot in mots:
        essai = f"{ligne} {mot}".strip()
        if dessin.textlength(essai, font=police) <= largeur_max or not ligne:
            ligne = essai
        else:
            lignes.append(ligne)
            ligne = mot
    if ligne:
        lignes.append(ligne)
    return lignes


def _tronquer_texte(dessin, texte: str, police, largeur_max: int) -> str:
    """Tronque un texte avec une ellipse s'il dépasse la largeur maximale."""
    if dessin.textlength(texte, font=police) <= largeur_max:
        return texte
    while texte and dessin.textlength(f"{texte}…", font=police) > largeur_max:
        texte = texte[:-1]
    return f"{texte.rstrip()}…"


def generer_image_resume(rumeur: Rumeur) -> RapportVerification:
    """Génère une carte PNG de synthèse avec Pillow."""
    from PIL import Image, ImageDraw

    rapport = getattr(rumeur, "rapport", None)
    if rapport is None:
        rapport = generer_rapport(rumeur)

    donnees = collecter_donnees_rapport(rumeur)
    premiere = donnees["premiere_publication"]

    largeur, hauteur = 1080, 1080
    fond = "#0f172a"
    couleur_accent = {
        RapportVerification.NiveauRisque.FAIBLE: "#22c55e",
        RapportVerification.NiveauRisque.MOYEN: "#f59e0b",
        RapportVerification.NiveauRisque.ELEVE: "#f97316",
        RapportVerification.NiveauRisque.TRES_ELEVE: "#ef4444",
    }.get(rapport.niveau_risque, "#38bdf8")

    image = Image.new("RGB", (largeur, hauteur), fond)
    dessin = ImageDraw.Draw(image)

    police_marque = _charger_police(34, gras=True)
    police_titre = _charger_police(50, gras=True)
    police_score = _charger_police(150, gras=True)
    police_libelle = _charger_police(28)
    police_valeur = _charger_police(34, gras=True)
    police_petit = _charger_police(26)
    police_pied = _charger_police(24, gras=True)

    marge = 76
    dessin.text((marge, 58), "FACTCHECK MADA", font=police_marque, fill="#38bdf8")
    dessin.text(
        (marge, 104),
        "Fiche de synthèse — aide à la décision",
        font=police_petit,
        fill="#94a3b8",
    )
    dessin.line((marge, 154, largeur - marge, 154), fill="#1e293b", width=3)

    lignes_titre = _decouper_texte(
        dessin,
        rumeur.titre,
        police_titre,
        largeur - 2 * marge,
    )
    titre_tronque = len(lignes_titre) > 3
    lignes_titre = lignes_titre[:3]
    if titre_tronque and lignes_titre:
        lignes_titre[-1] = _tronquer_texte(
            dessin,
            f"{lignes_titre[-1]}…",
            police_titre,
            largeur - 2 * marge,
        )

    position_y = 196
    for ligne in lignes_titre:
        dessin.text((marge, position_y), ligne, font=police_titre, fill="#f8fafc")
        position_y += 60

    dessin.text(
        (marge, 400),
        "INDICE DE CRÉDIBILITÉ",
        font=police_libelle,
        fill="#94a3b8",
    )
    dessin.text(
        (marge, 436),
        f"{rapport.score_credibilite}",
        font=police_score,
        fill=couleur_accent,
    )
    dessin.text(
        (marge + 310, 520),
        "/100",
        font=police_valeur,
        fill="#cbd5e1",
    )
    dessin.text(
        (marge, 618),
        f"Niveau de risque : {rapport.get_niveau_risque_display()}",
        font=police_valeur,
        fill=couleur_accent,
    )

    dessin.line((marge, 684, largeur - marge, 684), fill="#1e293b", width=3)

    nombre_publications = donnees["statistiques"]["nombre_publications"]
    plateformes = ", ".join(donnees["statistiques"]["plateformes"]) or "Aucune"
    premiere_date = (
        premiere["date_publication_lisible"] if premiere else "Non renseignée"
    )

    metriques = [
        ("Publications recensées", str(nombre_publications)),
        ("Plateformes", plateformes),
        ("Première publication", premiere_date),
    ]
    position_y = 716
    for libelle, valeur in metriques:
        dessin.text((marge, position_y), libelle, font=police_libelle, fill="#94a3b8")
        valeur_affichee = _tronquer_texte(
            dessin,
            valeur,
            police_valeur,
            largeur - 2 * marge,
        )
        dessin.text(
            (marge, position_y + 34),
            valeur_affichee,
            font=police_valeur,
            fill="#e2e8f0",
        )
        position_y += 74

    dessin.line(
        (marge, hauteur - 150, largeur - marge, hauteur - 150),
        fill="#1e293b",
        width=3,
    )
    dessin.text(
        (marge, hauteur - 126),
        "Analyse automatique — vérification humaine requise",
        font=police_pied,
        fill="#fbbf24",
    )
    dessin.text(
        (marge, hauteur - 90),
        "Document d'aide à la décision, sans verdict de vérité.",
        font=police_petit,
        fill="#94a3b8",
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    _enregistrer_fichier(
        rapport.fichier_image,
        f"rapport_{rumeur.id}.png",
        buffer.getvalue(),
    )
    return rapport
