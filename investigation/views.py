"""
Vues de l'API FactCheck Mada.

Les vues restent minces : elles valident les entrées, contrôlent les droits et
délèguent la logique métier aux services. Toutes les routes sont protégées par
JWT, sauf l'inscription, la connexion, le rafraîchissement et la santé.
"""

from __future__ import annotations

import os

from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from investigation.models import (
    PublicationSource,
    RapportVerification,
    Rumeur,
)
from investigation.pagination import PaginationFrancaise
from investigation.permissions import est_administrateur
from investigation.serializers import (
    AlerteCompteSerializer,
    AlerteTexteSerializer,
    ConnexionSerializer,
    InscriptionSerializer,
    JournalisteProfilSerializer,
    LienPropagationSerializer,
    PublicationSourceSerializer,
    RafraichirTokenSerializer,
    RapportVerificationSerializer,
    RumeurDetailSerializer,
    RumeurEcritureSerializer,
    RumeurListeSerializer,
    RumeurModificationSerializer,
)
from investigation.services.service_analyse_compte import analyser_compte
from investigation.services.service_analyse_texte import analyser_texte
from investigation.services.service_propagation import (
    construire_arbre_propagation,
    creer_liens_propagation,
    detecter_premiere_publication,
)
from investigation.services.service_rapport import (
    generer_image_resume,
    generer_pdf_rapport,
    generer_rapport,
)
from investigation.services.service_similarite import (
    SEUIL_DOUBLON_RUMEUR,
    calculer_empreinte,
    rechercher_doublon_exact,
    rechercher_rumeurs_similaires,
)

MESSAGE_DOUBLON = "Une rumeur similaire a déjà été enregistrée."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jetons_pour(journaliste) -> dict:
    """Construit une paire de jetons JWT avec les claims métier."""
    rafraichissement = RefreshToken.for_user(journaliste)
    rafraichissement["role"] = journaliste.role
    rafraichissement["redaction"] = journaliste.redaction
    acces = rafraichissement.access_token
    return {
        "jeton_acces": str(acces),
        "jeton_rafraichissement": str(rafraichissement),
    }


def _reponse_authentification(journaliste, message: str, code: int) -> Response:
    donnees = {
        "message": message,
        "journaliste": JournalisteProfilSerializer(
            journaliste,
            context={"request": None},
        ).data,
    }
    donnees.update(_jetons_pour(journaliste))
    return Response(donnees, status=code)


def _rumeurs_visibles(utilisateur):
    """Queryset des rumeurs accessibles à l'utilisateur connecté."""
    queryset = Rumeur.objects.all()
    if not est_administrateur(utilisateur):
        queryset = queryset.filter(cree_par=utilisateur)
    return queryset


def _queryset_detail_rumeur():
    """Queryset optimisé pour le détail complet d'une rumeur."""
    return Rumeur.objects.select_related("cree_par", "rapport").prefetch_related(
        "publications__alertes_compte",
        "alertes_texte",
        "liens_propagation",
    )


def _obtenir_rumeur(request, rumeur_id: int) -> Rumeur:
    """Retourne une rumeur du périmètre autorisé ou lève une 404 française."""
    rumeur = _rumeurs_visibles(request.user).filter(pk=rumeur_id).first()
    if rumeur is None:
        raise NotFound("Rumeur introuvable ou accès non autorisé.")
    return rumeur


def _obtenir_publication(request, publication_id: int) -> PublicationSource:
    """Retourne une publication du périmètre autorisé."""
    queryset = PublicationSource.objects.select_related("rumeur")
    if not est_administrateur(request.user):
        queryset = queryset.filter(rumeur__cree_par=request.user)
    publication = queryset.filter(pk=publication_id).first()
    if publication is None:
        raise NotFound("Publication introuvable ou accès non autorisé.")
    return publication


def _lire_date(request, nom: str):
    """Lit un paramètre de date AAAA-MM-JJ et valide son format."""
    valeur = request.query_params.get(nom)
    if not valeur:
        return None
    date = parse_date(valeur)
    if date is None:
        raise ValidationError(
            {nom: "Format de date invalide. Utilisez le format AAAA-MM-JJ."}
        )
    return date


# ---------------------------------------------------------------------------
# Santé
# ---------------------------------------------------------------------------

class SanteAPIView(APIView):
    """Endpoint public de vérification de disponibilité."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        return Response({"statut": "ok", "service": "API FactCheck Mada"})


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

class InscriptionAPIView(APIView):
    """Crée un compte journaliste et retourne immédiatement des jetons."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "authentification"

    def post(self, request):
        serializer = InscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        journaliste = serializer.save()
        return _reponse_authentification(
            journaliste,
            "Compte créé avec succès.",
            status.HTTP_201_CREATED,
        )


class ConnexionAPIView(APIView):
    """Authentifie un journaliste et retourne ses jetons JWT."""

    permission_classes = [AllowAny]
    throttle_scope = "authentification"

    def post(self, request):
        serializer = ConnexionSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        journaliste = serializer.validated_data["journaliste"]
        return _reponse_authentification(
            journaliste,
            "Connexion réussie.",
            status.HTTP_200_OK,
        )


class RafraichirTokenAPIView(APIView):
    """Renouvelle un jeton d'accès à partir du jeton de rafraîchissement."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "authentification"

    def post(self, request):
        serializer = RafraichirTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        jeton = serializer.validated_data["jeton"]
        return Response(
            {
                "jeton_acces": str(jeton.access_token),
                "message": "Jeton d'accès renouvelé.",
            }
        )


class ProfilAPIView(APIView):
    """Retourne le profil du journaliste connecté."""

    def get(self, request):
        return Response(
            JournalisteProfilSerializer(
                request.user,
                context={"request": request},
            ).data
        )


# ---------------------------------------------------------------------------
# Rumeurs
# ---------------------------------------------------------------------------

class RumeurListCreateView(ListCreateAPIView):
    """Liste les rumeurs du journaliste et gère la création avec doublons."""

    serializer_class = RumeurListeSerializer
    pagination_class = PaginationFrancaise

    def get_queryset(self):
        queryset = _rumeurs_visibles(self.request.user).select_related(
            "cree_par",
            "rapport",
        )
        queryset = queryset.annotate(
            nombre_publications_annote=Count("publications", distinct=True)
        )

        statut = self.request.query_params.get("statut")
        if statut:
            if statut not in Rumeur.Statut.values:
                raise ValidationError(
                    {
                        "statut": (
                            "Statut invalide. Valeurs autorisées : "
                            + ", ".join(Rumeur.Statut.values)
                            + "."
                        )
                    }
                )
            queryset = queryset.filter(statut=statut)

        titre = self.request.query_params.get("titre")
        if titre:
            queryset = queryset.filter(titre__icontains=titre.strip())

        recherche = self.request.query_params.get("recherche")
        if recherche:
            terme = recherche.strip()
            queryset = queryset.filter(
                Q(titre__icontains=terme) | Q(contenu__icontains=terme)
            )

        date_debut = _lire_date(self.request, "date_debut")
        date_fin = _lire_date(self.request, "date_fin")
        if date_debut:
            queryset = queryset.filter(cree_le__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(cree_le__date__lte=date_fin)

        tri = self.request.query_params.get("tri", "-cree_le")
        tris_autorises = {
            "cree_le",
            "-cree_le",
            "titre",
            "-titre",
            "statut",
            "-statut",
        }
        if tri not in tris_autorises:
            raise ValidationError(
                {
                    "tri": (
                        "Tri invalide. Valeurs autorisées : "
                        + ", ".join(sorted(tris_autorises))
                        + "."
                    )
                }
            )
        return queryset.order_by(tri)

    def create(self, request, *args, **kwargs):
        serializer = RumeurEcritureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donnees = serializer.validated_data
        contenu = donnees["contenu"]
        perimetre = _rumeurs_visibles(request.user)

        empreinte = calculer_empreinte(contenu)
        doublon = rechercher_doublon_exact(empreinte, queryset=perimetre)
        similaires = rechercher_rumeurs_similaires(
            contenu,
            queryset=perimetre,
            seuil=0.50,
            limite=3,
        )

        if doublon or (
            similaires
            and similaires[0]["score_similarite"] >= SEUIL_DOUBLON_RUMEUR
        ):
            identifiant = (
                doublon.id if doublon else similaires[0]["id"]
            )
            existante = _queryset_detail_rumeur().get(pk=identifiant)
            return Response(
                {
                    "cree": False,
                    "message": MESSAGE_DOUBLON,
                    "rumeur": RumeurDetailSerializer(
                        existante,
                        context={"request": request},
                    ).data,
                    "similaires": similaires,
                },
                status=status.HTTP_200_OK,
            )

        rumeur = Rumeur.objects.create(
            cree_par=request.user,
            **donnees,
        )
        rumeur = _queryset_detail_rumeur().get(pk=rumeur.pk)
        return Response(
            {
                "cree": True,
                "message": "Rumeur enregistrée.",
                "rumeur": RumeurDetailSerializer(
                    rumeur,
                    context={"request": request},
                ).data,
                "similaires": similaires,
            },
            status=status.HTTP_201_CREATED,
        )


class RumeurDetailView(RetrieveUpdateDestroyAPIView):
    """Consultation, modification et suppression d'une rumeur."""

    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return _queryset_detail_rumeur().filter(
            pk__in=_rumeurs_visibles(self.request.user).values("pk")
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return RumeurModificationSerializer
        return RumeurDetailSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        donnees = serializer.validated_data

        if "contenu" in donnees:
            perimetre = _rumeurs_visibles(request.user)
            empreinte = calculer_empreinte(donnees["contenu"])
            doublon = rechercher_doublon_exact(
                empreinte,
                queryset=perimetre,
                exclure_id=instance.pk,
            )
            similaires = rechercher_rumeurs_similaires(
                donnees["contenu"],
                queryset=perimetre,
                seuil=SEUIL_DOUBLON_RUMEUR,
                exclure_id=instance.pk,
                limite=3,
            )
            if doublon or similaires:
                return Response(
                    {
                        "detail": (
                            "Une rumeur similaire existe déjà. La modification "
                            "n'a pas été enregistrée."
                        ),
                        "similaires": similaires,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        for champ, valeur in donnees.items():
            setattr(instance, champ, valeur)
        instance.save()

        instance = _queryset_detail_rumeur().get(pk=instance.pk)
        return Response(
            RumeurDetailSerializer(
                instance,
                context={"request": request},
            ).data
        )


# ---------------------------------------------------------------------------
# Publications et propagation
# ---------------------------------------------------------------------------

class PublicationListCreateView(APIView):
    """Liste chronologique et création analysée d'une publication source."""

    def get(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        publications = rumeur.publications.prefetch_related(
            "alertes_compte"
        ).order_by("date_publication", "id")
        return Response(
            PublicationSourceSerializer(
                publications,
                many=True,
                context={"request": request},
            ).data
        )

    def post(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        serializer = PublicationSourceSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            publication = serializer.save(rumeur=rumeur)
            premiere = detecter_premiere_publication(rumeur)
            liens = creer_liens_propagation(publication)
            alertes_compte = analyser_compte(publication)
            resultat_texte = analyser_texte(rumeur)

        publication = PublicationSource.objects.prefetch_related(
            "alertes_compte"
        ).get(pk=publication.pk)

        return Response(
            {
                "message": "Publication enregistrée et analysée.",
                "publication": PublicationSourceSerializer(
                    publication,
                    context={"request": request},
                ).data,
                "liens_crees": LienPropagationSerializer(
                    liens,
                    many=True,
                ).data,
                "alertes_compte": AlerteCompteSerializer(
                    alertes_compte,
                    many=True,
                ).data,
                "analyse_texte": {
                    "score_risque_texte": resultat_texte["score_risque_texte"],
                    "nombre_alertes": resultat_texte["nombre_alertes"],
                    "alertes": AlerteTexteSerializer(
                        resultat_texte["alertes"],
                        many=True,
                    ).data,
                },
                "premiere_publication_detectee": (
                    PublicationSourceSerializer(
                        premiere,
                        context={"request": request},
                    ).data
                    if premiere
                    else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class ArbrePropagationView(APIView):
    """Retourne l'arbre de propagation prêt à être affiché par React."""

    def get(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        return Response(construire_arbre_propagation(rumeur))


class AnalyserCompteView(APIView):
    """Relance l'analyse des indices du compte d'une publication."""

    def post(self, request, publication_id: int):
        publication = _obtenir_publication(request, publication_id)
        alertes = analyser_compte(publication)
        return Response(
            {
                "publication_id": publication.id,
                "nombre_alertes": len(alertes),
                "alertes": AlerteCompteSerializer(alertes, many=True).data,
                "message": "Analyse du compte terminée.",
            }
        )


class AnalyserTexteView(APIView):
    """Relance l'analyse des indices présents dans le texte."""

    def post(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        resultat = analyser_texte(rumeur)
        return Response(
            {
                "rumeur_id": rumeur.id,
                "score_risque_texte": resultat["score_risque_texte"],
                "nombre_alertes": resultat["nombre_alertes"],
                "alertes": AlerteTexteSerializer(
                    resultat["alertes"],
                    many=True,
                ).data,
            }
        )


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

class GenererRapportView(APIView):
    """Génère ou met à jour la fiche de vérification."""

    def post(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        rapport = generer_rapport(rumeur)
        return Response(
            {
                "message": "Rapport généré.",
                "rapport": RapportVerificationSerializer(
                    rapport,
                    context={"request": request},
                ).data,
            }
        )


class RapportDetailView(APIView):
    """Retourne le rapport existant d'une rumeur."""

    def get(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        rapport = RapportVerification.objects.filter(rumeur=rumeur).first()
        if rapport is None:
            raise NotFound(
                "Aucun rapport n'a encore été généré pour cette rumeur."
            )
        return Response(
            RapportVerificationSerializer(
                rapport,
                context={"request": request},
            ).data
        )


class RapportPdfView(APIView):
    """Génère et télécharge le PDF du rapport."""

    def get(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        try:
            rapport = generer_pdf_rapport(rumeur)
        except ImportError:
            return Response(
                {
                    "detail": (
                        "Export PDF indisponible : la bibliothèque ReportLab "
                        "n'est pas installée."
                    )
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        if not rapport.fichier_pdf:
            return Response(
                {"detail": "Le fichier PDF n'a pas pu être généré."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return FileResponse(
            rapport.fichier_pdf.open("rb"),
            content_type="application/pdf",
            as_attachment=False,
            filename=os.path.basename(rapport.fichier_pdf.name),
        )


class RapportImageView(APIView):
    """Génère et télécharge la carte PNG de synthèse."""

    def get(self, request, rumeur_id: int):
        rumeur = _obtenir_rumeur(request, rumeur_id)
        try:
            rapport = generer_image_resume(rumeur)
        except ImportError:
            return Response(
                {
                    "detail": (
                        "Export image indisponible : la bibliothèque Pillow "
                        "n'est pas installée."
                    )
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        if not rapport.fichier_image:
            return Response(
                {"detail": "L'image n'a pas pu être générée."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return FileResponse(
            rapport.fichier_image.open("rb"),
            content_type="image/png",
            as_attachment=False,
            filename=os.path.basename(rapport.fichier_image.name),
        )


# ---------------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------------

class TableauDeBordView(APIView):
    """Statistiques agrégées du périmètre du journaliste connecté."""

    def get(self, request):
        rumeurs = _rumeurs_visibles(request.user)
        rapports = RapportVerification.objects.filter(rumeur__in=rumeurs)

        publications = PublicationSource.objects.filter(rumeur__in=rumeurs)
        total_publications = publications.count()

        repartition_requete = (
            publications.values("plateforme")
            .annotate(total=Count("id"))
            .order_by("-total", "plateforme")
        )
        repartition_plateformes = {
            ligne["plateforme"]: ligne["total"] for ligne in repartition_requete
        }
        plateforme_plus_active = (
            next(iter(repartition_plateformes), None)
            if repartition_plateformes
            else None
        )

        rumeurs_recentes = (
            rumeurs.select_related("rapport")
            .annotate(nombre_publications_annote=Count("publications", distinct=True))
            .order_by("-cree_le")[:5]
        )

        return Response(
            {
                "total_rumeurs": rumeurs.count(),
                "rumeurs_analysees": rapports.count(),
                "rumeurs_haut_risque": rapports.filter(
                    niveau_risque__in=[
                        RapportVerification.NiveauRisque.ELEVE,
                        RapportVerification.NiveauRisque.TRES_ELEVE,
                    ]
                ).count(),
                "total_publications": total_publications,
                "plateforme_plus_active": plateforme_plus_active,
                "repartition_plateformes": repartition_plateformes,
                "rumeurs_recentes": RumeurListeSerializer(
                    rumeurs_recentes,
                    many=True,
                    context={"request": request},
                ).data,
            }
        )
