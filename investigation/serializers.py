"""
Serializers de l'API FactCheck Mada.

Les messages de validation sont rédigés en français. Les champs calculés
(empreinte, première détection, alertes, rapport) sont en lecture seule.
"""

from __future__ import annotations

import os

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ErreurValidationDjango
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
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

TAILLE_MAX_CAPTURE = 5 * 1024 * 1024
EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# ---------------------------------------------------------------------------
# Journaliste et authentification
# ---------------------------------------------------------------------------

class JournalisteProfilSerializer(serializers.ModelSerializer):
    """Profil public d'un journaliste connecté."""

    nom_utilisateur = serializers.CharField(source="username", read_only=True)
    date_inscription = serializers.DateTimeField(source="date_joined", read_only=True)
    est_administrateur = serializers.BooleanField(read_only=True)

    class Meta:
        model = Journaliste
        fields = [
            "id",
            "nom_utilisateur",
            "email",
            "redaction",
            "role",
            "date_inscription",
            "est_administrateur",
        ]
        read_only_fields = fields


class InscriptionSerializer(serializers.Serializer):
    """Inscription publique : le rôle journaliste est imposé."""

    nom_utilisateur = serializers.CharField(max_length=150, min_length=3)
    email = serializers.EmailField(max_length=254)
    mot_de_passe = serializers.CharField(write_only=True, trim_whitespace=False)
    confirmation_mot_de_passe = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    redaction = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate_nom_utilisateur(self, valeur: str) -> str:
        valeur = valeur.strip()
        if Journaliste.objects.filter(username__iexact=valeur).exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )
        return valeur

    def validate_email(self, valeur: str) -> str:
        valeur = valeur.strip().lower()
        if Journaliste.objects.filter(email__iexact=valeur).exists():
            raise serializers.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return valeur

    def validate(self, attrs: dict) -> dict:
        if attrs["mot_de_passe"] != attrs["confirmation_mot_de_passe"]:
            raise serializers.ValidationError(
                {"confirmation_mot_de_passe": "Les deux mots de passe ne correspondent pas."}
            )

        utilisateur_temporaire = Journaliste(
            username=attrs["nom_utilisateur"],
            email=attrs["email"],
        )
        try:
            validate_password(attrs["mot_de_passe"], user=utilisateur_temporaire)
        except ErreurValidationDjango as erreur:
            raise serializers.ValidationError(
                {"mot_de_passe": list(erreur.messages)}
            ) from erreur
        return attrs

    def create(self, validated_data: dict) -> Journaliste:
        validated_data.pop("confirmation_mot_de_passe")
        mot_de_passe = validated_data.pop("mot_de_passe")
        return Journaliste.objects.create_user(
            username=validated_data["nom_utilisateur"],
            email=validated_data["email"],
            password=mot_de_passe,
            redaction=validated_data.get("redaction", ""),
            role=Journaliste.Role.JOURNALISTE,
        )


class ConnexionSerializer(serializers.Serializer):
    """Vérifie les identifiants et retourne le journaliste authentifié."""

    nom_utilisateur = serializers.CharField(max_length=150)
    mot_de_passe = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        journaliste = authenticate(
            request=self.context.get("request"),
            username=attrs["nom_utilisateur"].strip(),
            password=attrs["mot_de_passe"],
        )
        if journaliste is None:
            raise AuthenticationFailed(
                "Nom d'utilisateur ou mot de passe incorrect."
            )
        if not journaliste.is_active:
            raise AuthenticationFailed("Ce compte est désactivé.")
        attrs["journaliste"] = journaliste
        return attrs


class RafraichirTokenSerializer(serializers.Serializer):
    """Valide un jeton de rafraîchissement (nom français ou alias standard)."""

    jeton_rafraichissement = serializers.CharField(
        write_only=True,
        required=False,
    )
    refresh = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs: dict) -> dict:
        jeton = attrs.get("jeton_rafraichissement") or attrs.get("refresh")
        if not jeton:
            raise serializers.ValidationError(
                {
                    "jeton_rafraichissement": (
                        "Le jeton de rafraîchissement est obligatoire."
                    )
                }
            )
        try:
            attrs["jeton"] = RefreshToken(jeton)
        except TokenError as erreur:
            raise serializers.ValidationError(
                {
                    "jeton_rafraichissement": (
                        "Jeton de rafraîchissement invalide ou expiré."
                    )
                }
            ) from erreur
        return attrs


# ---------------------------------------------------------------------------
# Alertes et propagation
# ---------------------------------------------------------------------------

class AlerteCompteSerializer(serializers.ModelSerializer):
    type_libelle = serializers.CharField(
        source="get_type_alerte_display",
        read_only=True,
    )
    gravite_libelle = serializers.CharField(
        source="get_gravite_display",
        read_only=True,
    )

    class Meta:
        model = AlerteCompte
        fields = [
            "id",
            "type_alerte",
            "type_libelle",
            "gravite",
            "gravite_libelle",
            "description",
            "cree_le",
        ]
        read_only_fields = fields


class AlerteTexteSerializer(serializers.ModelSerializer):
    type_libelle = serializers.CharField(
        source="get_type_alerte_display",
        read_only=True,
    )
    gravite_libelle = serializers.CharField(
        source="get_gravite_display",
        read_only=True,
    )

    class Meta:
        model = AlerteTexte
        fields = [
            "id",
            "type_alerte",
            "type_libelle",
            "gravite",
            "gravite_libelle",
            "expression_detectee",
            "explication",
            "cree_le",
        ]
        read_only_fields = fields


class LienPropagationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LienPropagation
        fields = [
            "id",
            "publication_parent_id",
            "publication_enfant_id",
            "score_similarite",
            "detecte_le",
        ]
        read_only_fields = fields

    def validate_score_similarite(self, valeur: float) -> float:
        if not 0.0 <= valeur <= 1.0:
            raise serializers.ValidationError(
                "Le score de similarité doit être compris entre 0 et 1."
            )
        return valeur


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------

class PublicationSourceSerializer(serializers.ModelSerializer):
    plateforme_libelle = serializers.CharField(
        source="get_plateforme_display",
        read_only=True,
    )
    alertes_compte = AlerteCompteSerializer(many=True, read_only=True)
    rumeur = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PublicationSource
        fields = [
            "id",
            "rumeur",
            "plateforme",
            "plateforme_libelle",
            "url_publication",
            "nom_auteur",
            "url_profil_auteur",
            "date_creation_compte",
            "nombre_abonnes",
            "date_publication",
            "est_premiere_detection",
            "texte_brut",
            "capture_ecran",
            "cree_le",
            "alertes_compte",
        ]
        read_only_fields = [
            "id",
            "rumeur",
            "est_premiere_detection",
            "cree_le",
            "alertes_compte",
        ]

    def validate_date_creation_compte(self, valeur):
        if valeur and valeur > timezone.localdate():
            raise serializers.ValidationError(
                "La date de création du compte ne peut pas être dans le futur."
            )
        return valeur

    def validate_capture_ecran(self, valeur):
        if not valeur:
            return valeur
        if valeur.size > TAILLE_MAX_CAPTURE:
            raise serializers.ValidationError(
                "La capture d'écran ne doit pas dépasser 5 Mo."
            )
        extension = os.path.splitext(getattr(valeur, "name", ""))[1].lower()
        type_contenu = getattr(valeur, "content_type", "") or ""
        if extension not in EXTENSIONS_IMAGES:
            raise serializers.ValidationError(
                "Format d'image non accepté. Utilisez JPG, PNG, WEBP ou GIF."
            )
        if type_contenu and not type_contenu.startswith("image/"):
            raise serializers.ValidationError(
                "Le fichier envoyé n'est pas une image valide."
            )

        # Vérification réelle du contenu : l'extension et le Content-Type
        # peuvent être falsifiés par le client.
        try:
            from PIL import Image, UnidentifiedImageError

            image = Image.open(valeur)
            image.verify()
            valeur.seek(0)
        except (UnidentifiedImageError, OSError, ValueError) as erreur:
            raise serializers.ValidationError(
                "Le fichier envoyé n'est pas une image valide."
            ) from erreur
        return valeur


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

class RapportVerificationSerializer(serializers.ModelSerializer):
    niveau_risque_libelle = serializers.CharField(
        source="get_niveau_risque_display",
        read_only=True,
    )

    class Meta:
        model = RapportVerification
        fields = [
            "id",
            "score_credibilite",
            "niveau_risque",
            "niveau_risque_libelle",
            "resume",
            "recommandations",
            "genere_le",
            "fichier_pdf",
            "fichier_image",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Rumeurs
# ---------------------------------------------------------------------------

class RumeurListeSerializer(serializers.ModelSerializer):
    extrait_contenu = serializers.SerializerMethodField()
    langue_libelle = serializers.CharField(source="get_langue_display", read_only=True)
    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)
    nombre_publications = serializers.SerializerMethodField()
    score_credibilite = serializers.SerializerMethodField()
    niveau_risque = serializers.SerializerMethodField()
    niveau_risque_libelle = serializers.SerializerMethodField()

    class Meta:
        model = Rumeur
        fields = [
            "id",
            "titre",
            "extrait_contenu",
            "langue",
            "langue_libelle",
            "statut",
            "statut_libelle",
            "empreinte_contenu",
            "cree_le",
            "nombre_publications",
            "score_credibilite",
            "niveau_risque",
            "niveau_risque_libelle",
        ]
        read_only_fields = fields

    def get_extrait_contenu(self, objet: Rumeur) -> str:
        contenu = (objet.contenu or "").strip()
        if len(contenu) <= 180:
            return contenu
        return f"{contenu[:177].rstrip()}…"

    def get_nombre_publications(self, objet: Rumeur) -> int:
        valeur_annottee = getattr(objet, "nombre_publications_annote", None)
        if valeur_annottee is not None:
            return valeur_annottee
        return objet.publications.count()

    def _rapport(self, objet: Rumeur):
        try:
            return objet.rapport
        except RapportVerification.DoesNotExist:
            return None

    def get_score_credibilite(self, objet: Rumeur):
        rapport = self._rapport(objet)
        return rapport.score_credibilite if rapport else None

    def get_niveau_risque(self, objet: Rumeur):
        rapport = self._rapport(objet)
        return rapport.niveau_risque if rapport else None

    def get_niveau_risque_libelle(self, objet: Rumeur):
        rapport = self._rapport(objet)
        return rapport.get_niveau_risque_display() if rapport else None


class RumeurDetailSerializer(RumeurListeSerializer):
    publications = PublicationSourceSerializer(many=True, read_only=True)
    alertes_texte = AlerteTexteSerializer(many=True, read_only=True)
    liens_propagation = LienPropagationSerializer(many=True, read_only=True)
    rapport = RapportVerificationSerializer(read_only=True, allow_null=True)
    cree_par_nom = serializers.CharField(source="cree_par.username", read_only=True)

    class Meta(RumeurListeSerializer.Meta):
        fields = RumeurListeSerializer.Meta.fields + [
            "contenu",
            "cree_par",
            "cree_par_nom",
            "publications",
            "alertes_texte",
            "liens_propagation",
            "rapport",
        ]
        read_only_fields = fields


class RumeurEcritureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rumeur
        fields = ["titre", "contenu", "langue"]
        extra_kwargs = {
            "titre": {"required": True, "allow_blank": False, "max_length": 255},
            "contenu": {"required": True, "allow_blank": False},
            "langue": {"required": False},
        }

    def validate_titre(self, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise serializers.ValidationError("Le titre est obligatoire.")
        return valeur

    def validate_contenu(self, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise serializers.ValidationError("Le contenu est obligatoire.")
        return valeur


class RumeurModificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rumeur
        fields = ["titre", "contenu", "statut"]
        extra_kwargs = {
            "titre": {"required": False, "allow_blank": False},
            "contenu": {"required": False, "allow_blank": False},
            "statut": {"required": False},
        }

    def validate_titre(self, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise serializers.ValidationError("Le titre ne peut pas être vide.")
        return valeur

    def validate_contenu(self, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise serializers.ValidationError("Le contenu ne peut pas être vide.")
        return valeur
