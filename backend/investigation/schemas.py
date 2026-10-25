"""
Schémas de réponse réservés à la documentation OpenAPI.

Ces sérialiseurs ne sont pas utilisés pour le rendu normal de l'API : ils
décrivent précisément les réponses personnalisées afin que Swagger UI et
Redoc affichent des exemples complets et cohérents avec les vues.
"""

from __future__ import annotations

from rest_framework import serializers

from investigation.serializers import (
    AlerteCompteSerializer,
    AlerteTexteSerializer,
    JournalisteProfilSerializer,
    LienPropagationSerializer,
    PublicationSourceSerializer,
    RapportVerificationSerializer,
    RumeurDetailSerializer,
    RumeurListeSerializer,
)


class ReponseSanteSerializer(serializers.Serializer):
    """Réponse de l'endpoint public de santé."""

    statut = serializers.CharField()
    service = serializers.CharField()


class RumeurSimilaireSerializer(serializers.Serializer):
    """Rumeur proche retournée lors d'une création ou d'une modification."""

    id = serializers.IntegerField()
    titre = serializers.CharField()
    score_similarite = serializers.FloatField()
    cree_le = serializers.DateTimeField()
    statut = serializers.CharField()


class ReponseAuthentificationSerializer(serializers.Serializer):
    """Jetons et profil renvoyés après inscription ou connexion."""

    message = serializers.CharField()
    journaliste = JournalisteProfilSerializer()
    jeton_acces = serializers.CharField()
    jeton_rafraichissement = serializers.CharField()


class ReponseRafraichissementSerializer(serializers.Serializer):
    """Nouveau jeton d'accès après rafraîchissement."""

    jeton_acces = serializers.CharField()
    message = serializers.CharField()


class ReponseRumeurSerializer(serializers.Serializer):
    """Résultat d'une création de rumeur, avec ou sans doublon détecté."""

    cree = serializers.BooleanField()
    message = serializers.CharField()
    rumeur = RumeurDetailSerializer()
    similaires = RumeurSimilaireSerializer(many=True)


class AnalyseTextePublicationSerializer(serializers.Serializer):
    """Analyse de texte jointe à la création d'une publication."""

    score_risque_texte = serializers.IntegerField()
    nombre_alertes = serializers.IntegerField()
    alertes = AlerteTexteSerializer(many=True)


class ReponsePublicationSerializer(serializers.Serializer):
    """Résultat complet de l'ajout d'une publication source."""

    message = serializers.CharField()
    publication = PublicationSourceSerializer()
    liens_crees = LienPropagationSerializer(many=True)
    alertes_compte = AlerteCompteSerializer(many=True)
    analyse_texte = AnalyseTextePublicationSerializer()
    premiere_publication_detectee = PublicationSourceSerializer(allow_null=True)


class ReponseAnalyseCompteSerializer(serializers.Serializer):
    """Résultat d'une analyse manuelle de compte."""

    publication_id = serializers.IntegerField()
    nombre_alertes = serializers.IntegerField()
    alertes = AlerteCompteSerializer(many=True)
    message = serializers.CharField()


class ReponseAnalyseTexteSerializer(serializers.Serializer):
    """Résultat d'une analyse manuelle du texte d'une rumeur."""

    rumeur_id = serializers.IntegerField()
    score_risque_texte = serializers.IntegerField()
    nombre_alertes = serializers.IntegerField()
    alertes = AlerteTexteSerializer(many=True)


class NoeudPropagationSerializer(serializers.Serializer):
    """Nœud de l'arbre de propagation destiné à React."""

    id = serializers.IntegerField()
    plateforme = serializers.CharField()
    plateforme_libelle = serializers.CharField()
    nom_auteur = serializers.CharField()
    url_publication = serializers.CharField(allow_blank=True)
    date_publication = serializers.DateTimeField()
    est_premiere_detection = serializers.BooleanField()
    indicateurs_risque = serializers.ListField(
        child=serializers.CharField(),
    )
    nombre_alertes = serializers.IntegerField()


class LienArbreSerializer(serializers.Serializer):
    """Lien orienté entre deux nœuds de propagation."""

    publication_parent_id = serializers.IntegerField(allow_null=True)
    publication_enfant_id = serializers.IntegerField()
    score_similarite = serializers.FloatField()


class StatistiquesPropagationSerializer(serializers.Serializer):
    """Agrégats de diffusion d'une rumeur."""

    nombre_publications = serializers.IntegerField()
    plateformes = serializers.ListField(child=serializers.CharField())
    premiere_publication = serializers.CharField(allow_null=True)
    derniere_publication = serializers.CharField(allow_null=True)
    vitesse_estimee = serializers.CharField()
    duree_heures = serializers.FloatField()
    repartition_plateformes = serializers.DictField(
        child=serializers.IntegerField(),
    )


class ReponseArbrePropagationSerializer(serializers.Serializer):
    """Structure complète de l'arbre de propagation."""

    rumeur_id = serializers.IntegerField()
    premiere_publication_detectee = NoeudPropagationSerializer(allow_null=True)
    noeuds = NoeudPropagationSerializer(many=True)
    liens = LienArbreSerializer(many=True)
    statistiques_propagation = StatistiquesPropagationSerializer()


class ReponseRapportGenereSerializer(serializers.Serializer):
    """Rapport créé ou mis à jour."""

    message = serializers.CharField()
    rapport = RapportVerificationSerializer()


class ReponseTableauDeBordSerializer(serializers.Serializer):
    """Statistiques agrégées du périmètre du journaliste."""

    total_rumeurs = serializers.IntegerField()
    rumeurs_analysees = serializers.IntegerField()
    rumeurs_haut_risque = serializers.IntegerField()
    total_publications = serializers.IntegerField()
    plateforme_plus_active = serializers.CharField(allow_null=True)
    repartition_plateformes = serializers.DictField(
        child=serializers.IntegerField(),
    )
    rumeurs_recentes = RumeurListeSerializer(many=True)
