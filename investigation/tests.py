"""
Tests automatisés de FactCheck Mada.

Exécution : python manage.py test investigation -v 2
Les tests couvrent les services, l'authentification, l'isolation des données,
la propagation, les analyses et les rapports.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from investigation.models import (
    AlerteCompte,
    AlerteTexte,
    Journaliste,
    LienPropagation,
    PublicationSource,
    RapportVerification,
    Rumeur,
)
from investigation.services.service_analyse_texte import analyser_texte
from investigation.services.service_rapport import determiner_niveau_risque
from investigation.services.service_similarite import (
    calculer_empreinte,
    calculer_similarite,
    normaliser_texte,
    rechercher_rumeurs_similaires,
)

MOT_DE_PASSE = "MotDePasse123!"


def creer_journaliste(
    nom: str = "alice",
    email: str | None = None,
    role: str = Journaliste.Role.JOURNALISTE,
) -> Journaliste:
    """Crée un journaliste de test avec un mot de passe valide."""
    return Journaliste.objects.create_user(
        username=nom,
        email=email or f"{nom}@factcheck.mg",
        password=MOT_DE_PASSE,
        redaction="Rédaction de test",
        role=role,
    )


class BaseAPITest(APITestCase):
    """Socle commun : cache vidé et helpers d'authentification."""

    def setUp(self):
        cache.clear()

    def authentifier(self, journaliste: Journaliste) -> None:
        rafraichissement = RefreshToken.for_user(journaliste)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {rafraichissement.access_token}"
        )


# ---------------------------------------------------------------------------
# Services de similarité
# ---------------------------------------------------------------------------

class ServiceSimilariteTests(TestCase):
    def test_normalisation_supprime_accents_emojis_et_ponctuation(self):
        texte = "  ÉLÉPHANT 🐘, PÉNURIE!!!  de   carburant  "
        self.assertEqual(
            normaliser_texte(texte),
            "elephant penurie de carburant",
        )

    def test_empreinte_stable_et_sensible_au_contenu(self):
        empreinte_a = calculer_empreinte("Pénurie de carburant !")
        empreinte_b = calculer_empreinte("penurie de carburant")
        empreinte_c = calculer_empreinte("Coupure d'eau")
        self.assertEqual(empreinte_a, empreinte_b)
        self.assertNotEqual(empreinte_a, empreinte_c)
        self.assertEqual(len(empreinte_a), 64)

    def test_similarite_textes_identiques_et_vides(self):
        self.assertEqual(calculer_similarite("Bonjour", "Bonjour"), 1.0)
        self.assertEqual(calculer_similarite("", "Bonjour"), 0.0)
        self.assertEqual(calculer_similarite(None, None), 0.0)

    def test_similarite_forte_pour_une_version_proche(self):
        texte = (
            "Urgence : une pénurie de carburant touche Antananarivo. "
            "Partagez ce message à tous vos contacts avant qu'ils suppriment "
            "l'information."
        )
        variante = (
            "Urgence : une pénurie de carburant touche Antananarivo. "
            "Partagez ce message à tous vos contacts avant qu'ils suppriment "
            "l'information. Selon nos informations."
        )
        self.assertGreaterEqual(calculer_similarite(texte, variante), 0.90)

    def test_similarite_faible_pour_des_textes_differents(self):
        score = calculer_similarite(
            "Pénurie de carburant à Antananarivo",
            "Le match de football a été reporté à Toamasina",
        )
        self.assertLess(score, 0.50)

    def test_recherche_similaires_triee_et_exclusion(self):
        auteur = creer_journaliste()
        cible = Rumeur.objects.create(
            titre="Carburant",
            contenu="Urgence : pénurie de carburant à Antananarivo.",
            cree_par=auteur,
        )
        proche = Rumeur.objects.create(
            titre="Carburant bis",
            contenu="Urgence : pénurie de carburant à Antananarivo. Partagez.",
            cree_par=auteur,
        )
        Rumeur.objects.create(
            titre="Football",
            contenu="Le match de football a été reporté à Toamasina.",
            cree_par=auteur,
        )

        resultats = rechercher_rumeurs_similaires(
            cible.contenu,
            queryset=Rumeur.objects.filter(cree_par=auteur),
            exclure_id=cible.id,
        )

        self.assertEqual(resultats[0]["id"], proche.id)
        self.assertNotIn(cible.id, [element["id"] for element in resultats])
        self.assertEqual(
            resultats,
            sorted(resultats, key=lambda element: -element["score_similarite"]),
        )


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

class AuthentificationTests(BaseAPITest):
    def test_sante_est_publique(self):
        reponse = self.client.get(reverse("investigation:sante"))
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["statut"], "ok")

    def test_inscription_retourne_des_jetons_et_un_role_journaliste(self):
        reponse = self.client.post(
            reverse("investigation:inscription"),
            {
                "nom_utilisateur": "nouveau",
                "email": "nouveau@factcheck.mg",
                "mot_de_passe": MOT_DE_PASSE,
                "confirmation_mot_de_passe": MOT_DE_PASSE,
                "redaction": "Nouvelle rédaction",
                "role": "administrateur",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 201)
        self.assertIn("jeton_acces", reponse.data)
        self.assertIn("jeton_rafraichissement", reponse.data)
        journaliste = Journaliste.objects.get(username="nouveau")
        self.assertEqual(journaliste.role, Journaliste.Role.JOURNALISTE)

    def test_inscription_refuse_les_mots_de_passe_differents(self):
        reponse = self.client.post(
            reverse("investigation:inscription"),
            {
                "nom_utilisateur": "nouveau",
                "email": "nouveau@factcheck.mg",
                "mot_de_passe": MOT_DE_PASSE,
                "confirmation_mot_de_passe": "AutreMotDePasse123!",
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("confirmation_mot_de_passe", reponse.data)

    def test_inscription_refuse_un_nom_deja_utilise(self):
        creer_journaliste("existant")
        reponse = self.client.post(
            reverse("investigation:inscription"),
            {
                "nom_utilisateur": "existant",
                "email": "autre@factcheck.mg",
                "mot_de_passe": MOT_DE_PASSE,
                "confirmation_mot_de_passe": MOT_DE_PASSE,
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("nom_utilisateur", reponse.data)

    def test_connexion_et_mauvais_mot_de_passe(self):
        journaliste = creer_journaliste()
        bonne = self.client.post(
            reverse("investigation:connexion"),
            {"nom_utilisateur": journaliste.username, "mot_de_passe": MOT_DE_PASSE},
            format="json",
        )
        self.assertEqual(bonne.status_code, 200)
        self.assertEqual(bonne.data["journaliste"]["nom_utilisateur"], "alice")

        mauvaise = self.client.post(
            reverse("investigation:connexion"),
            {"nom_utilisateur": journaliste.username, "mot_de_passe": "Faux123!"},
            format="json",
        )
        self.assertEqual(mauvaise.status_code, 401)

    def test_rafraichissement_du_jeton(self):
        journaliste = creer_journaliste()
        jeton = RefreshToken.for_user(journaliste)
        reponse = self.client.post(
            reverse("investigation:rafraichir_token"),
            {"jeton_rafraichissement": str(jeton)},
            format="json",
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("jeton_acces", reponse.data)

    def test_profil_protege(self):
        sans_jeton = self.client.get(reverse("investigation:profil"))
        self.assertEqual(sans_jeton.status_code, 401)

        journaliste = creer_journaliste()
        self.authentifier(journaliste)
        avec_jeton = self.client.get(reverse("investigation:profil"))
        self.assertEqual(avec_jeton.status_code, 200)
        self.assertEqual(avec_jeton.data["nom_utilisateur"], "alice")


# ---------------------------------------------------------------------------
# Rumeurs
# ---------------------------------------------------------------------------

class RumeurAPITests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.alice = creer_journaliste("alice")
        self.bob = creer_journaliste("bob")
        self.authentifier(self.alice)

    def creer_rumeur_api(self, titre="Pénurie de carburant", contenu=None):
        return self.client.post(
            reverse("investigation:rumeurs"),
            {
                "titre": titre,
                "contenu": contenu
                or (
                    "Urgence : une pénurie de carburant toucherait "
                    "Antananarivo. Partagez ce message avant qu'ils suppriment "
                    "l'information."
                ),
                "langue": "fr",
            },
            format="json",
        )

    def test_creation_rumeur(self):
        reponse = self.creer_rumeur_api()
        self.assertEqual(reponse.status_code, 201)
        self.assertTrue(reponse.data["cree"])
        rumeur = Rumeur.objects.get()
        self.assertEqual(rumeur.cree_par, self.alice)
        self.assertEqual(len(rumeur.empreinte_contenu), 64)
        self.assertEqual(
            reponse.data["rumeur"]["empreinte_contenu"],
            rumeur.empreinte_contenu,
        )

    def test_doublon_exact_retourne_la_rumeur_existante(self):
        premiere = self.creer_rumeur_api()
        seconde = self.creer_rumeur_api()
        self.assertEqual(premiere.status_code, 201)
        self.assertEqual(seconde.status_code, 200)
        self.assertFalse(seconde.data["cree"])
        self.assertEqual(
            seconde.data["message"],
            "Une rumeur similaire a déjà été enregistrée.",
        )
        self.assertEqual(seconde.data["rumeur"]["id"], premiere.data["rumeur"]["id"])
        self.assertEqual(Rumeur.objects.count(), 1)

    def test_doublon_quasi_identique(self):
        self.creer_rumeur_api()
        reponse = self.creer_rumeur_api(
            titre="Autre titre",
            contenu=(
                "Urgence : une pénurie de carburant toucherait "
                "Antananarivo. Partagez ce message avant qu'ils suppriment "
                "l'information. Selon nos informations."
            ),
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(Rumeur.objects.count(), 1)

    def test_liste_isolee_par_journaliste_et_paginee(self):
        self.creer_rumeur_api()
        Rumeur.objects.create(
            titre="Rumeur de Bob",
            contenu="Un contenu totalement différent sur le football.",
            cree_par=self.bob,
        )
        reponse = self.client.get(reverse("investigation:rumeurs"))
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["total"], 1)
        self.assertIn("resultats", reponse.data)
        self.assertEqual(reponse.data["resultats"][0]["titre"], "Pénurie de carburant")

    def test_filtres_et_recherche(self):
        self.creer_rumeur_api()
        Rumeur.objects.create(
            titre="Coupure d'eau",
            contenu="Une coupure d'eau est annoncée à Toamasina.",
            cree_par=self.alice,
            statut=Rumeur.Statut.ARCHIVEE,
        )
        self.authentifier(self.alice)

        par_statut = self.client.get(
            reverse("investigation:rumeurs"),
            {"statut": Rumeur.Statut.ARCHIVEE},
        )
        self.assertEqual(par_statut.data["total"], 1)

        par_recherche = self.client.get(
            reverse("investigation:rumeurs"),
            {"recherche": "carburant"},
        )
        self.assertEqual(par_recherche.data["total"], 1)

        date_invalide = self.client.get(
            reverse("investigation:rumeurs"),
            {"date_debut": "hier"},
        )
        self.assertEqual(date_invalide.status_code, 400)

    def test_detail_modification_et_suppression(self):
        creation = self.creer_rumeur_api()
        identifiant = creation.data["rumeur"]["id"]
        url = reverse("investigation:rumeur_detail", kwargs={"pk": identifiant})

        detail = self.client.get(url)
        self.assertEqual(detail.status_code, 200)
        for cle in (
            "publications",
            "alertes_texte",
            "liens_propagation",
            "rapport",
        ):
            self.assertIn(cle, detail.data)

        modification = self.client.patch(
            url,
            {"titre": "Titre modifié", "statut": Rumeur.Statut.ANALYSE_TERMINEE},
            format="json",
        )
        self.assertEqual(modification.status_code, 200)
        self.assertEqual(modification.data["titre"], "Titre modifié")

        suppression = self.client.delete(url)
        self.assertEqual(suppression.status_code, 204)
        self.assertFalse(Rumeur.objects.filter(pk=identifiant).exists())

    def test_modification_refuse_un_doublon(self):
        self.creer_rumeur_api(titre="Première")
        seconde = self.creer_rumeur_api(
            titre="Seconde",
            contenu="Un texte totalement différent sur le sport à Madagascar.",
        )
        identifiant = seconde.data["rumeur"]["id"]
        reponse = self.client.patch(
            reverse("investigation:rumeur_detail", kwargs={"pk": identifiant}),
            {
                "contenu": (
                    "Urgence : une pénurie de carburant toucherait "
                    "Antananarivo. Partagez ce message avant qu'ils suppriment "
                    "l'information."
                )
            },
            format="json",
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertIn("detail", reponse.data)

    def test_acces_aux_rumeurs_d_un_autre_journaliste_interdit(self):
        rumeur_bob = Rumeur.objects.create(
            titre="Rumeur de Bob",
            contenu="Contenu de Bob sur le football.",
            cree_par=self.bob,
        )
        reponse = self.client.get(
            reverse("investigation:rumeur_detail", kwargs={"pk": rumeur_bob.id})
        )
        self.assertEqual(reponse.status_code, 404)

    def test_admin_voit_toutes_les_rumeurs(self):
        Rumeur.objects.create(
            titre="Rumeur de Bob",
            contenu="Contenu de Bob sur le football.",
            cree_par=self.bob,
        )
        administrateur = creer_journaliste(
            "admin",
            role=Journaliste.Role.ADMINISTRATEUR,
        )
        self.authentifier(administrateur)
        reponse = self.client.get(reverse("investigation:rumeurs"))
        self.assertEqual(reponse.data["total"], 1)


# ---------------------------------------------------------------------------
# Propagation et analyses
# ---------------------------------------------------------------------------

class PropagationTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.journaliste = creer_journaliste()
        self.authentifier(self.journaliste)
        self.rumeur = Rumeur.objects.create(
            titre="Pénurie de carburant",
            contenu=(
                "Urgence : une pénurie de carburant toucherait Antananarivo. "
                "Partagez ce message avant qu'ils suppriment l'information."
            ),
            cree_par=self.journaliste,
        )

    def ajouter_publication(
        self,
        texte: str,
        jours: int = 0,
        nom_auteur: str = "Alerte Info Madagascar",
        **extra,
    ):
        donnees = {
            "plateforme": "facebook",
            "url_publication": "https://facebook.com/posts/1",
            "nom_auteur": nom_auteur,
            "url_profil_auteur": "https://facebook.com/profil",
            "date_creation_compte": (timezone.localdate() - timedelta(days=10)),
            "nombre_abonnes": 150,
            "date_publication": (
                timezone.now() - timedelta(days=jours)
            ).isoformat(),
            "texte_brut": texte,
        }
        donnees.update(extra)
        return self.client.post(
            reverse(
                "investigation:publications",
                kwargs={"rumeur_id": self.rumeur.id},
            ),
            donnees,
            format="json",
        )

    def test_creation_publication_et_premiere_detection(self):
        texte = "Urgence : pénurie de carburant à Antananarivo. Partagez."
        premiere = self.ajouter_publication(texte, jours=3)
        self.assertEqual(premiere.status_code, 201)
        publication = PublicationSource.objects.get(id=premiere.data["publication"]["id"])
        self.assertTrue(publication.est_premiere_detection)
        self.assertIn("alertes_compte", premiere.data["publication"])

    def test_lien_de_propagation_et_mise_a_jour_source_zero(self):
        texte = (
            "Urgence : une pénurie de carburant toucherait Antananarivo. "
            "Partagez ce message avant qu'ils suppriment l'information."
        )
        self.ajouter_publication(texte, jours=2)
        self.ajouter_publication(
            f"{texte} Selon nos informations.",
            jours=1,
        )
        self.assertEqual(LienPropagation.objects.count(), 1)

        self.ajouter_publication(texte, jours=4)
        self.assertEqual(LienPropagation.objects.count(), 2)
        premiere = self.rumeur.publications.get(est_premiere_detection=True)
        self.assertEqual(
            premiere.date_publication.date(),
            (timezone.now() - timedelta(days=4)).date(),
        )

    def test_arbre_de_propagation(self):
        texte = (
            "Urgence : une pénurie de carburant toucherait Antananarivo. "
            "Partagez ce message avant qu'ils suppriment l'information."
        )
        self.ajouter_publication(texte, jours=3)
        self.ajouter_publication(f"{texte} Selon nos informations.", jours=1)

        reponse = self.client.get(
            reverse(
                "investigation:arbre_propagation",
                kwargs={"rumeur_id": self.rumeur.id},
            )
        )
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["rumeur_id"], self.rumeur.id)
        self.assertEqual(len(reponse.data["noeuds"]), 2)
        self.assertEqual(len(reponse.data["liens"]), 1)
        self.assertEqual(
            reponse.data["statistiques_propagation"]["nombre_publications"],
            2,
        )
        self.assertIn("facebook", reponse.data["statistiques_propagation"]["plateformes"])
        self.assertIsNotNone(reponse.data["premiere_publication_detectee"])

    def test_analyse_compte_regles_et_idempotence(self):
        reponse = self.ajouter_publication(
            "Texte de publication.",
            nom_auteur="Alerte Info Urgence",
            nombre_abonnes=20,
            url_profil_auteur="",
        )
        self.assertEqual(reponse.status_code, 201)
        publication = PublicationSource.objects.get(id=reponse.data["publication"]["id"])
        types = set(
            AlerteCompte.objects.filter(publication_source=publication).values_list(
                "type_alerte", flat=True
            )
        )
        self.assertIn(AlerteCompte.TypeAlerte.COMPTE_RECENT, types)
        self.assertIn(AlerteCompte.TypeAlerte.FAIBLE_ACTIVITE, types)
        self.assertIn(AlerteCompte.TypeAlerte.NOM_IMPOSTEUR, types)

        url = reverse(
            "investigation:analyser_compte",
            kwargs={"publication_id": publication.id},
        )
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(
            AlerteCompte.objects.filter(publication_source=publication).count(),
            len(types),
        )

    def test_analyse_texte_types_et_idempotence(self):
        rumeur = Rumeur.objects.create(
            titre="Alerte",
            contenu=(
                "URGENCE : danger ! Une grave pénurie. Partagez ce message à "
                "tous, avant 24h. Une aide de 500 000 ariary est offerte."
            ),
            cree_par=self.journaliste,
        )
        url = reverse(
            "investigation:analyser_texte",
            kwargs={"rumeur_id": rumeur.id},
        )
        premiere = self.client.post(url)
        self.assertEqual(premiere.status_code, 200)
        self.assertGreater(premiere.data["score_risque_texte"], 0)
        types = set(
            AlerteTexte.objects.filter(rumeur=rumeur).values_list(
                "type_alerte",
                flat=True,
            )
        )
        self.assertIn(AlerteTexte.TypeAlerte.LANGAGE_ALARMISTE, types)
        self.assertIn(AlerteTexte.TypeAlerte.APPEL_AU_PARTAGE, types)
        self.assertIn(AlerteTexte.TypeAlerte.PROMESSE_FINANCIERE, types)
        self.assertIn(AlerteTexte.TypeAlerte.ABSENCE_DE_SOURCE, types)

        nombre = AlerteTexte.objects.filter(rumeur=rumeur).count()
        self.client.post(url)
        self.assertEqual(AlerteTexte.objects.filter(rumeur=rumeur).count(), nombre)

    def test_publication_d_un_autre_journaliste_interdite(self):
        reponse = self.ajouter_publication("Texte.")
        publication_id = reponse.data["publication"]["id"]

        autre = creer_journaliste("autre")
        self.authentifier(autre)
        reponse = self.client.post(
            reverse(
                "investigation:analyser_compte",
                kwargs={"publication_id": publication_id},
            )
        )
        self.assertEqual(reponse.status_code, 404)

    def test_publication_sans_texte_ne_cree_pas_de_lien(self):
        self.ajouter_publication("", jours=2)
        self.ajouter_publication("", jours=1)
        self.assertEqual(LienPropagation.objects.count(), 0)

    def test_upload_capture_ecran(self):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="factcheck_captures_") as dossier:
            with override_settings(MEDIA_ROOT=dossier):
                buffer = BytesIO()
                Image.new("RGB", (32, 32), "#2563eb").save(buffer, format="PNG")
                capture = SimpleUploadedFile(
                    "capture.png",
                    buffer.getvalue(),
                    content_type="image/png",
                )
                reponse = self.client.post(
                    reverse(
                        "investigation:publications",
                        kwargs={"rumeur_id": self.rumeur.id},
                    ),
                    {
                        "plateforme": "facebook",
                        "nom_auteur": "Compte avec capture",
                        "date_publication": timezone.now().isoformat(),
                        "texte_brut": "Publication avec capture.",
                        "capture_ecran": capture,
                    },
                    format="multipart",
                )
                self.assertEqual(reponse.status_code, 201)
                self.assertIn(
                    "/media/captures/",
                    reponse.data["publication"]["capture_ecran"],
                )


# ---------------------------------------------------------------------------
# Rapports et tableau de bord
# ---------------------------------------------------------------------------

class RapportTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.media = tempfile.mkdtemp(prefix="factcheck_media_")
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(shutil.rmtree, self.media, True)

        self.journaliste = creer_journaliste()
        self.authentifier(self.journaliste)
        self.rumeur = Rumeur.objects.create(
            titre="Alerte prétendue sur une pénurie de carburant",
            contenu=(
                "URGENCE : une grave pénurie de carburant toucherait "
                "Antananarivo. Partagez ce message à tous, avant qu'ils "
                "suppriment l'information."
            ),
            cree_par=self.journaliste,
        )
        for index, jours in enumerate((3, 2, 1)):
            publication = PublicationSource.objects.create(
                rumeur=self.rumeur,
                plateforme="facebook" if index < 2 else "whatsapp",
                nom_auteur=f"Alerte Info {index}" if index == 0 else f"Compte {index}",
                url_profil_auteur="https://facebook.com/profil" if index == 0 else "",
                date_creation_compte=(
                    timezone.localdate() - timedelta(days=10)
                    if index == 0
                    else None
                ),
                nombre_abonnes=50 if index == 0 else None,
                date_publication=timezone.now() - timedelta(days=jours),
                texte_brut=(
                    "Urgence : pénurie de carburant à Antananarivo. "
                    "Partagez ce message à tous."
                ),
            )
            from investigation.services.service_analyse_compte import (
                analyser_compte,
            )
            from investigation.services.service_propagation import (
                creer_liens_propagation,
                detecter_premiere_publication,
            )

            detecter_premiere_publication(self.rumeur)
            creer_liens_propagation(publication)
            analyser_compte(publication)
        analyser_texte(self.rumeur)

    def test_niveaux_de_risque(self):
        self.assertEqual(determiner_niveau_risque(100), "faible")
        self.assertEqual(determiner_niveau_risque(80), "faible")
        self.assertEqual(determiner_niveau_risque(79), "moyen")
        self.assertEqual(determiner_niveau_risque(60), "moyen")
        self.assertEqual(determiner_niveau_risque(59), "eleve")
        self.assertEqual(determiner_niveau_risque(40), "eleve")
        self.assertEqual(determiner_niveau_risque(39), "tres_eleve")
        self.assertEqual(determiner_niveau_risque(0), "tres_eleve")

    def test_generation_rapport_complet_et_idempotent(self):
        url = reverse(
            "investigation:generer_rapport",
            kwargs={"rumeur_id": self.rumeur.id},
        )
        premiere = self.client.post(url)
        self.assertEqual(premiere.status_code, 200)
        rapport = premiere.data["rapport"]
        self.assertGreaterEqual(rapport["score_credibilite"], 0)
        self.assertLessEqual(rapport["score_credibilite"], 100)
        self.assertEqual(
            rapport["niveau_risque"],
            determiner_niveau_risque(rapport["score_credibilite"]),
        )
        self.assertIn("indices", rapport["resume"])
        self.assertIn("Contacter la source originale.", rapport["recommandations"])
        self.assertIn(
            "Ne pas publier sans confirmation officielle.",
            rapport["recommandations"],
        )

        seconde = self.client.post(url)
        self.assertEqual(seconde.status_code, 200)
        self.rumeur.refresh_from_db()
        self.assertEqual(
            RapportVerification.objects.filter(rumeur=self.rumeur).count(),
            1,
        )

    def test_consultation_rapport_absent_et_present(self):
        url = reverse("investigation:rapport", kwargs={"rumeur_id": self.rumeur.id})
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.post(
            reverse(
                "investigation:generer_rapport",
                kwargs={"rumeur_id": self.rumeur.id},
            )
        )
        reponse = self.client.get(url)
        self.assertEqual(reponse.status_code, 200)
        self.assertIn("score_credibilite", reponse.data)

    def test_exports_pdf_et_image(self):
        pdf = self.client.get(
            reverse(
                "investigation:rapport_pdf",
                kwargs={"rumeur_id": self.rumeur.id},
            )
        )
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        contenu_pdf = b"".join(pdf.streaming_content)
        self.assertTrue(contenu_pdf.startswith(b"%PDF"))

        image = self.client.get(
            reverse(
                "investigation:rapport_image",
                kwargs={"rumeur_id": self.rumeur.id},
            )
        )
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image["Content-Type"], "image/png")
        contenu_image = b"".join(image.streaming_content)
        self.assertTrue(contenu_image.startswith(b"\x89PNG"))

    def test_tableau_de_bord(self):
        self.client.post(
            reverse(
                "investigation:generer_rapport",
                kwargs={"rumeur_id": self.rumeur.id},
            )
        )
        reponse = self.client.get(reverse("investigation:tableau_de_bord"))
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.data["total_rumeurs"], 1)
        self.assertEqual(reponse.data["rumeurs_analysees"], 1)
        self.assertEqual(reponse.data["total_publications"], 3)
        self.assertEqual(reponse.data["plateforme_plus_active"], "facebook")
        self.assertEqual(len(reponse.data["rumeurs_recentes"]), 1)
        self.assertIn("rumeurs_haut_risque", reponse.data)

    def test_tableau_de_bord_isole(self):
        autre = creer_journaliste("autre")
        Rumeur.objects.create(
            titre="Chez l'autre",
            contenu="Contenu different.",
            cree_par=autre,
        )
        self.authentifier(autre)
        reponse = self.client.get(reverse("investigation:tableau_de_bord"))
        self.assertEqual(reponse.data["total_rumeurs"], 1)
        self.assertEqual(reponse.data["total_publications"], 0)


# ---------------------------------------------------------------------------
# Documentation OpenAPI
# ---------------------------------------------------------------------------

class DocumentationTests(APITestCase):
    """Vérifie que la documentation interactive est exposée et cohérente."""

    def setUp(self):
        cache.clear()

    def test_schema_openapi_est_accessible_et_contient_les_routes(self):
        reponse = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(reponse.status_code, 200)
        schema = reponse.json()
        self.assertEqual(schema["openapi"], "3.0.3")
        self.assertIn("/api/rumeurs/", schema["paths"])
        self.assertIn(
            "/api/rumeurs/{rumeur_id}/arbre-propagation/",
            schema["paths"],
        )
        self.assertIn("/api/tableau-de-bord/statistiques/", schema["paths"])

    def test_swagger_ui_est_accessible(self):
        reponse = self.client.get(reverse("swagger-ui"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "swagger-ui")

    def test_schema_documente_le_multipart_des_captures(self):
        reponse = self.client.get(
            reverse("schema"),
            HTTP_ACCEPT="application/json",
        )
        schema = reponse.json()
        operation = schema["paths"][
            "/api/rumeurs/{rumeur_id}/publications/"
        ]["post"]
        self.assertIn("multipart/form-data", operation["requestBody"]["content"])


# ---------------------------------------------------------------------------
# Commande de démonstration
# ---------------------------------------------------------------------------

class AdminTests(TestCase):
    def setUp(self):
        self.administrateur = Journaliste.objects.create_superuser(
            username="superadmin",
            email="superadmin@factcheck.mg",
            password=MOT_DE_PASSE,
        )
        self.client.force_login(self.administrateur)

    def test_pages_admin_accessibles(self):
        urls = [
            reverse("admin:index"),
            reverse("admin:investigation_journaliste_changelist"),
            reverse("admin:investigation_rumeur_changelist"),
            reverse("admin:investigation_rumeur_add"),
            reverse("admin:investigation_publicationsource_changelist"),
            reverse("admin:investigation_lienpropagation_changelist"),
            reverse("admin:investigation_alertecompte_changelist"),
            reverse("admin:investigation_alertetexte_changelist"),
            reverse("admin:investigation_rapportverification_changelist"),
        ]
        for url in urls:
            with self.subTest(url=url):
                reponse = self.client.get(url)
                self.assertEqual(reponse.status_code, 200)


class SeedDemoTests(TestCase):
    def test_seed_idempotent(self):
        from io import StringIO

        from django.core.management import call_command

        sortie = StringIO()
        call_command("seed_donnees_demo", stdout=sortie)
        nombre = Rumeur.objects.count()
        self.assertEqual(nombre, 3)
        self.assertTrue(Journaliste.objects.filter(username="demo").exists())

        call_command("seed_donnees_demo", stdout=StringIO())
        self.assertEqual(Rumeur.objects.count(), nombre)
