"""Routes de l'API d'investigation, toutes nommées en français."""

from django.urls import path

from investigation.views import (
    AnalyserCompteView,
    AnalyserTexteView,
    ArbrePropagationView,
    ConnexionAPIView,
    GenererRapportView,
    InscriptionAPIView,
    ProfilAPIView,
    PublicationListCreateView,
    RafraichirTokenAPIView,
    RapportDetailView,
    RapportImageView,
    RapportPdfView,
    RumeurDetailView,
    RumeurListCreateView,
    SanteAPIView,
    TableauDeBordView,
)

app_name = "investigation"

urlpatterns = [
    # Santé
    path("sante/", SanteAPIView.as_view(), name="sante"),
    # Authentification
    path(
        "authentification/inscription/",
        InscriptionAPIView.as_view(),
        name="inscription",
    ),
    path(
        "authentification/connexion/",
        ConnexionAPIView.as_view(),
        name="connexion",
    ),
    path(
        "authentification/rafraichir-token/",
        RafraichirTokenAPIView.as_view(),
        name="rafraichir_token",
    ),
    path(
        "authentification/profil/",
        ProfilAPIView.as_view(),
        name="profil",
    ),
    # Rumeurs
    path("rumeurs/", RumeurListCreateView.as_view(), name="rumeurs"),
    path(
        "rumeurs/<int:pk>/",
        RumeurDetailView.as_view(),
        name="rumeur_detail",
    ),
    # Publications et propagation
    path(
        "rumeurs/<int:rumeur_id>/publications/",
        PublicationListCreateView.as_view(),
        name="publications",
    ),
    path(
        "rumeurs/<int:rumeur_id>/arbre-propagation/",
        ArbrePropagationView.as_view(),
        name="arbre_propagation",
    ),
    path(
        "publications/<int:publication_id>/analyser-compte/",
        AnalyserCompteView.as_view(),
        name="analyser_compte",
    ),
    # Analyses du texte et rapport
    path(
        "rumeurs/<int:rumeur_id>/analyser-texte/",
        AnalyserTexteView.as_view(),
        name="analyser_texte",
    ),
    path(
        "rumeurs/<int:rumeur_id>/generer-rapport/",
        GenererRapportView.as_view(),
        name="generer_rapport",
    ),
    path(
        "rumeurs/<int:rumeur_id>/rapport/",
        RapportDetailView.as_view(),
        name="rapport",
    ),
    path(
        "rumeurs/<int:rumeur_id>/rapport/pdf/",
        RapportPdfView.as_view(),
        name="rapport_pdf",
    ),
    path(
        "rumeurs/<int:rumeur_id>/rapport/image/",
        RapportImageView.as_view(),
        name="rapport_image",
    ),
    # Tableau de bord
    path(
        "tableau-de-bord/statistiques/",
        TableauDeBordView.as_view(),
        name="tableau_de_bord",
    ),
]
