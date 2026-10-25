"""
Modèles métier de FactCheck Mada.

Tous les noms de modèles, champs et relations sont en français, à l'exception
des champs hérités d'AbstractUser (username, password, etc.) imposés par Django.
L'application ne produit jamais de verdict de vérité : elle stocke des indices
et des alertes destinés à la décision humaine.
"""

from __future__ import annotations

import os
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def chemin_capture_ecran(instance: PublicationSource, nom_fichier: str) -> str:
    """Génère un chemin de stockage sûr et unique pour une capture d'écran."""
    extension = os.path.splitext(nom_fichier)[1].lower()[:10]
    return f"captures/{uuid4().hex}{extension}"


def chemin_pdf_rapport(instance: RapportVerification, nom_fichier: str) -> str:
    """Génère un chemin de stockage pour le PDF d'un rapport."""
    return f"rapports/pdf/rapport_{instance.rumeur_id}.pdf"


def chemin_image_rapport(instance: RapportVerification, nom_fichier: str) -> str:
    """Génère un chemin de stockage pour l'image de synthèse d'un rapport."""
    return f"rapports/images/rapport_{instance.rumeur_id}.png"


# ---------------------------------------------------------------------------
# Journaliste
# ---------------------------------------------------------------------------

class Journaliste(AbstractUser):
    """Utilisateur de la plateforme, rattaché à une rédaction."""

    class Role(models.TextChoices):
        JOURNALISTE = "journaliste", "Journaliste"
        REDACTEUR_EN_CHEF = "redacteur_en_chef", "Rédacteur en chef"
        ADMINISTRATEUR = "administrateur", "Administrateur"

    email = models.EmailField("adresse e-mail", unique=True)
    redaction = models.CharField("rédaction", max_length=150, blank=True)
    role = models.CharField(
        "rôle",
        max_length=30,
        choices=Role.choices,
        default=Role.JOURNALISTE,
    )

    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "journaliste"
        verbose_name_plural = "journalistes"
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    @property
    def est_administrateur(self) -> bool:
        """Indique si l'utilisateur peut consulter les données de toutes les rédactions."""
        return bool(self.is_staff or self.is_superuser or self.role == self.Role.ADMINISTRATEUR)


# ---------------------------------------------------------------------------
# Rumeur
# ---------------------------------------------------------------------------

class Rumeur(models.Model):
    """Information en cours d'investigation, saisie par un journaliste."""

    class Statut(models.TextChoices):
        EN_ANALYSE = "en_analyse", "En analyse"
        ANALYSE_TERMINEE = "analyse_terminee", "Analyse terminée"
        ARCHIVEE = "archivee", "Archivée"

    class Langue(models.TextChoices):
        FRANCAIS = "fr", "Français"
        MALAGASY = "mg", "Malagasy"
        ANGLAIS = "en", "Anglais"
        AUTRE = "autre", "Autre"

    titre = models.CharField("titre", max_length=255)
    contenu = models.TextField("contenu")
    empreinte_contenu = models.CharField(
        "empreinte du contenu (SHA-256)",
        max_length=64,
        blank=True,
        db_index=True,
        editable=False,
    )
    langue = models.CharField(
        "langue",
        max_length=10,
        choices=Langue.choices,
        default=Langue.FRANCAIS,
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rumeurs",
        verbose_name="créée par",
    )
    cree_le = models.DateTimeField("créée le", auto_now_add=True, db_index=True)
    statut = models.CharField(
        "statut",
        max_length=30,
        choices=Statut.choices,
        default=Statut.EN_ANALYSE,
        db_index=True,
    )

    class Meta:
        verbose_name = "rumeur"
        verbose_name_plural = "rumeurs"
        ordering = ["-cree_le"]
        indexes = [
            models.Index(fields=["cree_par", "-cree_le"], name="rumeur_auteur_date_idx"),
            models.Index(fields=["statut", "-cree_le"], name="rumeur_statut_date_idx"),
        ]

    def __str__(self) -> str:
        return self.titre

    def save(self, *args, **kwargs):
        """Calcule systématiquement l'empreinte du texte normalisé."""
        # Import tardif pour éviter un cycle entre modèles et services.
        from investigation.services.service_similarite import calculer_empreinte

        self.empreinte_contenu = calculer_empreinte(self.contenu)
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Publication source
# ---------------------------------------------------------------------------

class PublicationSource(models.Model):
    """Publication publique saisie manuellement par le journaliste."""

    class Plateforme(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        MESSENGER = "messenger", "Messenger"
        WHATSAPP = "whatsapp", "WhatsApp"
        TIKTOK = "tiktok", "TikTok"
        YOUTUBE = "youtube", "YouTube"
        SITE_WEB = "site_web", "Site web"
        AUTRE = "autre", "Autre"

    rumeur = models.ForeignKey(
        Rumeur,
        on_delete=models.CASCADE,
        related_name="publications",
        verbose_name="rumeur",
    )
    plateforme = models.CharField(
        "plateforme",
        max_length=20,
        choices=Plateforme.choices,
        db_index=True,
    )
    url_publication = models.URLField(
        "URL de la publication",
        max_length=500,
        blank=True,
    )
    nom_auteur = models.CharField("nom de l'auteur", max_length=200)
    url_profil_auteur = models.URLField(
        "URL du profil de l'auteur",
        max_length=500,
        blank=True,
    )
    date_creation_compte = models.DateField(
        "date de création du compte",
        null=True,
        blank=True,
    )
    nombre_abonnes = models.PositiveIntegerField(
        "nombre d'abonnés",
        null=True,
        blank=True,
    )
    date_publication = models.DateTimeField("date de publication", db_index=True)
    est_premiere_detection = models.BooleanField(
        "première détection",
        default=False,
        db_index=True,
        editable=False,
    )
    texte_brut = models.TextField("texte brut", blank=True)
    capture_ecran = models.ImageField(
        "capture d'écran",
        upload_to=chemin_capture_ecran,
        blank=True,
        null=True,
    )
    cree_le = models.DateTimeField("enregistrée le", auto_now_add=True)

    class Meta:
        verbose_name = "publication source"
        verbose_name_plural = "publications sources"
        ordering = ["date_publication", "id"]
        indexes = [
            models.Index(
                fields=["rumeur", "date_publication"],
                name="publication_rumeur_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_plateforme_display()} — {self.nom_auteur}"


# ---------------------------------------------------------------------------
# Propagation
# ---------------------------------------------------------------------------

class LienPropagation(models.Model):
    """Lien de similarité entre deux publications d'une même rumeur."""

    rumeur = models.ForeignKey(
        Rumeur,
        on_delete=models.CASCADE,
        related_name="liens_propagation",
        verbose_name="rumeur",
    )
    publication_parent = models.ForeignKey(
        PublicationSource,
        on_delete=models.SET_NULL,
        related_name="liens_sortants",
        verbose_name="publication parente",
        null=True,
        blank=True,
    )
    publication_enfant = models.ForeignKey(
        PublicationSource,
        on_delete=models.CASCADE,
        related_name="liens_entrants",
        verbose_name="publication enfant",
    )
    score_similarite = models.FloatField(
        "score de similarité",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    detecte_le = models.DateTimeField("détecté le", auto_now_add=True)

    class Meta:
        verbose_name = "lien de propagation"
        verbose_name_plural = "liens de propagation"
        ordering = ["detecte_le", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(score_similarite__gte=0.0, score_similarite__lte=1.0),
                name="lien_score_entre_0_et_1",
            ),
            models.CheckConstraint(
                condition=~Q(publication_parent=F("publication_enfant")),
                name="lien_parent_different_enfant",
            ),
            models.UniqueConstraint(
                fields=["publication_parent", "publication_enfant"],
                name="lien_unique_parent_enfant",
            ),
            # Une publication ne peut avoir qu'un seul parent dans l'arbre.
            models.UniqueConstraint(
                fields=["publication_enfant"],
                name="lien_unique_parent_par_enfant",
            ),
        ]

    def __str__(self) -> str:
        parent = self.publication_parent_id or "?"
        return f"{parent} → {self.publication_enfant_id} ({self.score_similarite:.2f})"


# ---------------------------------------------------------------------------
# Alertes
# ---------------------------------------------------------------------------

class AlerteCompte(models.Model):
    """Signal d'alerte calculé sur le compte à l'origine d'une publication."""

    class TypeAlerte(models.TextChoices):
        COMPTE_RECENT = "compte_recent", "Compte récent"
        FAIBLE_ACTIVITE = "faible_activite", "Faible activité"
        NOM_IMPOSTEUR = "nom_imposteur", "Nom trompeur"
        PROFIL_ANONYME = "profil_anonyme", "Profil anonyme"
        COMPORTEMENT_SUSPECT = "comportement_suspect", "Comportement suspect"
        AUTRE = "autre", "Autre"

    class Gravite(models.TextChoices):
        FAIBLE = "faible", "Faible"
        MOYENNE = "moyenne", "Moyenne"
        ELEVEE = "elevee", "Élevée"

    publication_source = models.ForeignKey(
        PublicationSource,
        on_delete=models.CASCADE,
        related_name="alertes_compte",
        verbose_name="publication source",
    )
    type_alerte = models.CharField(
        "type d'alerte",
        max_length=30,
        choices=TypeAlerte.choices,
        db_index=True,
    )
    gravite = models.CharField(
        "gravité",
        max_length=10,
        choices=Gravite.choices,
        default=Gravite.MOYENNE,
    )
    description = models.TextField("description")
    cree_le = models.DateTimeField("créée le", auto_now_add=True)

    class Meta:
        verbose_name = "alerte de compte"
        verbose_name_plural = "alertes de compte"
        ordering = ["-cree_le", "id"]

    def __str__(self) -> str:
        return f"{self.get_type_alerte_display()} ({self.get_gravite_display()})"


class AlerteTexte(models.Model):
    """Signal d'alerte détecté dans le texte d'une rumeur."""

    class TypeAlerte(models.TextChoices):
        LANGAGE_ALARMISTE = "langage_alarmiste", "Langage alarmiste"
        APPEL_AU_PARTAGE = "appel_au_partage", "Appel au partage"
        ABSENCE_DE_SOURCE = "absence_de_source", "Absence de source"
        PROMESSE_FINANCIERE = "promesse_financiere", "Promesse financière"
        URGENCE_ARTIFICIELLE = "urgence_artificielle", "Urgence artificielle"
        CONTENU_SENSIBLE = "contenu_sensible", "Contenu sensible"
        AUTRE = "autre", "Autre"

    class Gravite(models.TextChoices):
        FAIBLE = "faible", "Faible"
        MOYENNE = "moyenne", "Moyenne"
        ELEVEE = "elevee", "Élevée"

    rumeur = models.ForeignKey(
        Rumeur,
        on_delete=models.CASCADE,
        related_name="alertes_texte",
        verbose_name="rumeur",
    )
    type_alerte = models.CharField(
        "type d'alerte",
        max_length=30,
        choices=TypeAlerte.choices,
        db_index=True,
    )
    gravite = models.CharField(
        "gravité",
        max_length=10,
        choices=Gravite.choices,
        default=Gravite.MOYENNE,
    )
    expression_detectee = models.CharField(
        "expression détectée",
        max_length=255,
        blank=True,
    )
    explication = models.TextField("explication")
    cree_le = models.DateTimeField("créée le", auto_now_add=True)

    class Meta:
        verbose_name = "alerte de texte"
        verbose_name_plural = "alertes de texte"
        ordering = ["-cree_le", "id"]
        indexes = [
            models.Index(
                fields=["rumeur", "type_alerte"],
                name="alerte_texte_rumeur_type_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_alerte_display()} — {self.expression_detectee}"


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

class RapportVerification(models.Model):
    """Fiche de synthèse destinée à la salle de rédaction."""

    class NiveauRisque(models.TextChoices):
        FAIBLE = "faible", "Faible"
        MOYEN = "moyen", "Moyen"
        ELEVE = "eleve", "Élevé"
        TRES_ELEVE = "tres_eleve", "Très élevé"

    rumeur = models.OneToOneField(
        Rumeur,
        on_delete=models.CASCADE,
        related_name="rapport",
        verbose_name="rumeur",
    )
    score_credibilite = models.PositiveSmallIntegerField(
        "score de crédibilité (0-100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    niveau_risque = models.CharField(
        "niveau de risque",
        max_length=20,
        choices=NiveauRisque.choices,
        db_index=True,
    )
    resume = models.TextField("résumé")
    recommandations = models.JSONField(
        "recommandations",
        default=list,
        blank=True,
    )
    genere_le = models.DateTimeField("généré le", auto_now=True)
    fichier_pdf = models.FileField(
        "fichier PDF",
        upload_to=chemin_pdf_rapport,
        blank=True,
        null=True,
    )
    fichier_image = models.FileField(
        "fichier image",
        upload_to=chemin_image_rapport,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "rapport de vérification"
        verbose_name_plural = "rapports de vérification"
        ordering = ["-genere_le"]
        constraints = [
            models.CheckConstraint(
                condition=Q(score_credibilite__gte=0, score_credibilite__lte=100),
                name="rapport_score_entre_0_et_100",
            ),
        ]

    def __str__(self) -> str:
        return f"Rapport — {self.rumeur.titre} ({self.score_credibilite}/100)"


# ---------------------------------------------------------------------------
# Nettoyage des fichiers médias
# ---------------------------------------------------------------------------

@receiver(post_delete, sender=PublicationSource)
def supprimer_capture_ecran(sender, instance: PublicationSource, **kwargs):
    """Supprime la capture d'écran du stockage lors de la suppression."""
    if instance.capture_ecran:
        instance.capture_ecran.delete(save=False)


@receiver(post_delete, sender=RapportVerification)
def supprimer_fichiers_rapport(sender, instance: RapportVerification, **kwargs):
    """Supprime les exports PDF et image lors de la suppression du rapport."""
    for champ in (instance.fichier_pdf, instance.fichier_image):
        if champ:
            champ.delete(save=False)
