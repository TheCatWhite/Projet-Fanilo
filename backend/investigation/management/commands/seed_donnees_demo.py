"""
Commande de démonstration : python manage.py seed_donnees_demo

Crée deux journalistes, trois rumeurs et des publications réalistes, puis
exécute les services d'analyse et de propagation. La commande est idempotente.
"""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from investigation.models import Journaliste, PublicationSource, Rumeur
from investigation.services.service_analyse_compte import analyser_compte
from investigation.services.service_analyse_texte import analyser_texte
from investigation.services.service_propagation import (
    creer_liens_propagation,
    detecter_premiere_publication,
)
from investigation.services.service_rapport import generer_rapport

TITRES_DEMO = [
    "Alerte prétendue sur une pénurie de carburant à Antananarivo",
    "Aide financière de 500 000 ariary annoncée sur WhatsApp",
    "Rumeur ancienne sur une coupure d'eau à Toamasina",
]

TEXTE_CARBURANT = (
    "URGENCE : une grave pénurie de carburant toucherait Antananarivo dès "
    "aujourd'hui. Les stations seraient fermées et les files d'attente "
    "deviendraient dangereuses. Partagez ce message à tous vos contacts avant "
    "qu'ils suppriment l'information. Ne gardez pas cela pour vous : envoyez à "
    "tous, c'est pour votre sécurité."
)

TEXTE_AIDE = (
    "Bonne nouvelle : une aide financière de 500 000 ariary est offerte à tous "
    "les habitants. Pour recevoir l'argent, envoyez votre numéro Mvola et "
    "partagez le message à 10 personnes. C'est gratuit et c'est une dernière "
    "chance, avant 24h seulement. Fanomezana ho an'ny rehetra : alefaso ny "
    "vaovao amin'ny namana."
)

TEXTE_EAU = (
    "Une coupure d'eau de plusieurs jours est annoncée à Toamasina. Les "
    "autorités n'ont pas communiqué, mais des habitants affirment avoir vu les "
    "vannes fermées. Transmettez l'information à vos proches."
)


class Command(BaseCommand):
    help = "Crée un jeu de données de démonstration pour FactCheck Mada."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reinitialiser",
            action="store_true",
            help="Supprime puis recrée les rumeurs de démonstration.",
        )

    def handle(self, *args, **options):
        reinitialiser = options["reinitialiser"]

        journaliste_demo, cree = Journaliste.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@factcheck.mg",
                "redaction": "La Gazette de Madagascar",
                "role": Journaliste.Role.JOURNALISTE,
            },
        )
        if cree:
            journaliste_demo.set_password("Demo1234!")
            journaliste_demo.save()

        redacteur, cree = Journaliste.objects.get_or_create(
            username="redaction",
            defaults={
                "email": "redaction@factcheck.mg",
                "redaction": "Rédaction centrale",
                "role": Journaliste.Role.REDACTEUR_EN_CHEF,
            },
        )
        if cree:
            redacteur.set_password("Demo1234!")
            redacteur.save()

        existe = Rumeur.objects.filter(
            cree_par=journaliste_demo,
            titre__in=TITRES_DEMO,
        ).exists()
        if existe and not reinitialiser:
            self.stdout.write(
                self.style.WARNING(
                    "Les données de démonstration existent déjà. "
                    "Utilisez --reinitialiser pour les recréer."
                )
            )
            self._afficher_identifiants()
            return
        if reinitialiser:
            Rumeur.objects.filter(
                cree_par=journaliste_demo,
                titre__in=TITRES_DEMO,
            ).delete()
            self.stdout.write("Anciennes données de démonstration supprimées.")

        maintenant = timezone.now()

        # ------------------------------------------------------------------
        # Rumeur 1 : carburant, quatre publications, rapport complet
        # ------------------------------------------------------------------
        rumeur_carburant = Rumeur.objects.create(
            titre=TITRES_DEMO[0],
            contenu=TEXTE_CARBURANT,
            langue=Rumeur.Langue.FRANCAIS,
            cree_par=journaliste_demo,
            statut=Rumeur.Statut.EN_ANALYSE,
        )

        publications_carburant = [
            {
                "plateforme": PublicationSource.Plateforme.FACEBOOK,
                "url_publication": "https://facebook.com/posts/alerte-carburant-001",
                "nom_auteur": "Alerte Info Madagascar",
                "url_profil_auteur": "https://facebook.com/alerte.info.madagascar",
                "date_creation_compte": (maintenant - timedelta(days=12)).date(),
                "nombre_abonnes": 120,
                "date_publication": maintenant - timedelta(days=4),
                "texte_brut": TEXTE_CARBURANT,
                "capture_ecran": None,
            },
            {
                "plateforme": PublicationSource.Plateforme.WHATSAPP,
                "url_publication": "",
                "nom_auteur": "Groupe Vazaha News",
                "url_profil_auteur": "",
                "date_creation_compte": None,
                "nombre_abonnes": None,
                "date_publication": maintenant - timedelta(days=3),
                "texte_brut": (
                    "URGENCE : une grave pénurie de carburant toucherait "
                    "Antananarivo. Les stations seraient fermées. Partagez ce "
                    "message à tous vos contacts avant qu'ils suppriment "
                    "l'information. Ne gardez pas cela pour vous, c'est pour "
                    "votre sécurité."
                ),
                "capture_ecran": None,
            },
            {
                "plateforme": PublicationSource.Plateforme.TIKTOK,
                "url_publication": "https://tiktok.com/@loza_vaovao/video/123456",
                "nom_auteur": "loza_vaovao",
                "url_profil_auteur": "https://tiktok.com/@loza_vaovao",
                "date_creation_compte": (maintenant - timedelta(days=20)).date(),
                "nombre_abonnes": 80,
                "date_publication": maintenant - timedelta(days=1),
                "texte_brut": (
                    "URGENCE : une grave pénurie de carburant toucherait "
                    "Antananarivo. Les stations seraient fermées et les files "
                    "d'attente deviendraient dangereuses. Partagez ce message "
                    "à tous vos contacts avant qu'ils suppriment l'information. "
                    "Ne gardez pas cela pour vous : envoyez à tous, c'est pour "
                    "votre sécurité."
                ),
                "capture_ecran": None,
            },
            {
                "plateforme": PublicationSource.Plateforme.SITE_WEB,
                "url_publication": "https://mada-actualites.mg/carburant-urgence",
                "nom_auteur": "Mada Actualités",
                "url_profil_auteur": "https://mada-actualites.mg/a-propos",
                "date_creation_compte": (maintenant - timedelta(days=420)).date(),
                "nombre_abonnes": 5200,
                "date_publication": maintenant - timedelta(hours=6),
                "texte_brut": (
                    "Une pénurie de carburant est signalée à Antananarivo. "
                    "Selon des témoignages, plusieurs stations seraient "
                    "fermées. Nous recherchons une confirmation officielle."
                ),
                "capture_ecran": None,
            },
        ]
        self._creer_publications(rumeur_carburant, publications_carburant)
        analyser_texte(rumeur_carburant)
        generer_rapport(rumeur_carburant)

        # ------------------------------------------------------------------
        # Rumeur 2 : aide financière, deux publications
        # ------------------------------------------------------------------
        rumeur_aide = Rumeur.objects.create(
            titre=TITRES_DEMO[1],
            contenu=TEXTE_AIDE,
            langue=Rumeur.Langue.FRANCAIS,
            cree_par=journaliste_demo,
            statut=Rumeur.Statut.EN_ANALYSE,
        )
        self._creer_publications(
            rumeur_aide,
            [
                {
                    "plateforme": PublicationSource.Plateforme.WHATSAPP,
                    "url_publication": "",
                    "nom_auteur": "Aide Officielle Mada",
                    "url_profil_auteur": "",
                    "date_creation_compte": (maintenant - timedelta(days=8)).date(),
                    "nombre_abonnes": 45,
                    "date_publication": maintenant - timedelta(days=2),
                    "texte_brut": TEXTE_AIDE,
                    "capture_ecran": None,
                },
                {
                    "plateforme": PublicationSource.Plateforme.FACEBOOK,
                    "url_publication": "https://facebook.com/posts/aide-mvola-500",
                    "nom_auteur": "Mada Solidarité",
                    "url_profil_auteur": "https://facebook.com/mada.solidarite",
                    "date_creation_compte": (maintenant - timedelta(days=60)).date(),
                    "nombre_abonnes": 340,
                    "date_publication": maintenant - timedelta(hours=12),
                    "texte_brut": (
                        "Bonne nouvelle : une aide financière de 500 000 ariary "
                        "est offerte aux habitants. Envoyez votre numéro Mvola "
                        "et partagez le message à 10 personnes. C'est gratuit, "
                        "une dernière chance avant 24h."
                    ),
                    "capture_ecran": None,
                },
            ],
        )
        analyser_texte(rumeur_aide)
        generer_rapport(rumeur_aide)

        # ------------------------------------------------------------------
        # Rumeur 3 : archive avec une seule publication
        # ------------------------------------------------------------------
        rumeur_eau = Rumeur.objects.create(
            titre=TITRES_DEMO[2],
            contenu=TEXTE_EAU,
            langue=Rumeur.Langue.FRANCAIS,
            cree_par=journaliste_demo,
            statut=Rumeur.Statut.ARCHIVEE,
        )
        self._creer_publications(
            rumeur_eau,
            [
                {
                    "plateforme": PublicationSource.Plateforme.FACEBOOK,
                    "url_publication": "https://facebook.com/posts/eau-toamasina",
                    "nom_auteur": "Toamasina Info",
                    "url_profil_auteur": "https://facebook.com/toamasina.info",
                    "date_creation_compte": (maintenant - timedelta(days=900)).date(),
                    "nombre_abonnes": 1800,
                    "date_publication": maintenant - timedelta(days=45),
                    "texte_brut": TEXTE_EAU,
                    "capture_ecran": None,
                }
            ],
        )
        analyser_texte(rumeur_eau)

        self.stdout.write(
            self.style.SUCCESS(
                "Données de démonstration créées : "
                f"{Rumeur.objects.filter(cree_par=journaliste_demo).count()} rumeurs."
            )
        )
        self._afficher_identifiants()

    def _creer_publications(self, rumeur: Rumeur, donnees: list[dict]) -> None:
        """Crée les publications puis exécute propagation et analyses."""
        for element in donnees:
            publication = PublicationSource.objects.create(
                rumeur=rumeur,
                **element,
            )
            detecter_premiere_publication(rumeur)
            creer_liens_propagation(publication)
            analyser_compte(publication)
        detecter_premiere_publication(rumeur)

    def _afficher_identifiants(self) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Comptes de démonstration :"))
        self.stdout.write("  - demo / Demo1234! (journaliste)")
        self.stdout.write("  - redaction / Demo1234! (rédacteur en chef)")
