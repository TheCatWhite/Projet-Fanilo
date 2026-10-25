"""Configuration de l'administration Django pour toutes les tables métier."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from investigation.models import (
    AlerteCompte,
    AlerteTexte,
    Journaliste,
    LienPropagation,
    PublicationSource,
    RapportVerification,
    Rumeur,
)

# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class AlerteCompteInline(admin.TabularInline):
    model = AlerteCompte
    extra = 0
    fields = ("type_alerte", "gravite", "description", "cree_le")
    readonly_fields = ("cree_le",)


class PublicationSourceInline(admin.TabularInline):
    model = PublicationSource
    extra = 0
    fields = (
        "plateforme",
        "nom_auteur",
        "date_publication",
        "est_premiere_detection",
        "nombre_abonnes",
    )
    readonly_fields = ("est_premiere_detection",)
    show_change_link = True


class AlerteTexteInline(admin.TabularInline):
    model = AlerteTexte
    extra = 0
    fields = (
        "type_alerte",
        "gravite",
        "expression_detectee",
        "explication",
        "cree_le",
    )
    readonly_fields = ("cree_le",)


class RapportVerificationInline(admin.StackedInline):
    model = RapportVerification
    extra = 0
    max_num = 1
    fields = (
        "score_credibilite",
        "niveau_risque",
        "resume",
        "recommandations",
        "fichier_pdf",
        "fichier_image",
        "genere_le",
    )
    readonly_fields = ("genere_le",)


# ---------------------------------------------------------------------------
# Journaliste
# ---------------------------------------------------------------------------

@admin.register(Journaliste)
class JournalisteAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "redaction",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active", "redaction")
    search_fields = ("username", "email", "redaction")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Informations rédactionnelles",
            {"fields": ("redaction", "role")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Informations rédactionnelles",
            {"fields": ("email", "redaction", "role")},
        ),
    )


# ---------------------------------------------------------------------------
# Rumeur et publications
# ---------------------------------------------------------------------------

@admin.register(Rumeur)
class RumeurAdmin(admin.ModelAdmin):
    list_display = ("titre", "cree_par", "statut", "cree_le")
    list_filter = ("statut", "langue", "cree_le")
    search_fields = ("titre", "contenu", "empreinte_contenu")
    readonly_fields = ("empreinte_contenu", "cree_le")
    date_hierarchy = "cree_le"
    inlines = [PublicationSourceInline, AlerteTexteInline, RapportVerificationInline]
    fieldsets = (
        ("Contenu", {"fields": ("titre", "contenu", "langue")}),
        ("Suivi", {"fields": ("statut", "cree_par", "cree_le", "empreinte_contenu")}),
    )


@admin.register(PublicationSource)
class PublicationSourceAdmin(admin.ModelAdmin):
    list_display = (
        "rumeur",
        "plateforme",
        "nom_auteur",
        "date_publication",
        "est_premiere_detection",
    )
    list_filter = ("plateforme", "est_premiere_detection", "date_publication")
    search_fields = ("nom_auteur", "texte_brut", "url_publication")
    readonly_fields = ("est_premiere_detection", "cree_le")
    date_hierarchy = "date_publication"
    inlines = [AlerteCompteInline]
    autocomplete_fields = ("rumeur",)
    fieldsets = (
        ("Identification", {"fields": ("rumeur", "plateforme", "url_publication")}),
        (
            "Auteur",
            {
                "fields": (
                    "nom_auteur",
                    "url_profil_auteur",
                    "date_creation_compte",
                    "nombre_abonnes",
                )
            },
        ),
        (
            "Publication",
            {
                "fields": (
                    "date_publication",
                    "texte_brut",
                    "capture_ecran",
                    "est_premiere_detection",
                    "cree_le",
                )
            },
        ),
    )


@admin.register(LienPropagation)
class LienPropagationAdmin(admin.ModelAdmin):
    list_display = (
        "rumeur",
        "publication_parent",
        "publication_enfant",
        "score_similarite",
        "detecte_le",
    )
    list_filter = ("rumeur", "detecte_le")
    search_fields = ("rumeur__titre",)
    readonly_fields = ("detecte_le",)
    autocomplete_fields = ("rumeur", "publication_parent", "publication_enfant")


# ---------------------------------------------------------------------------
# Alertes
# ---------------------------------------------------------------------------

@admin.register(AlerteCompte)
class AlerteCompteAdmin(admin.ModelAdmin):
    list_display = (
        "publication_source",
        "type_alerte",
        "gravite",
        "cree_le",
    )
    list_filter = ("type_alerte", "gravite", "cree_le")
    search_fields = ("publication_source__nom_auteur", "description")
    readonly_fields = ("cree_le",)
    autocomplete_fields = ("publication_source",)


@admin.register(AlerteTexte)
class AlerteTexteAdmin(admin.ModelAdmin):
    list_display = ("rumeur", "type_alerte", "gravite", "expression_detectee", "cree_le")
    list_filter = ("type_alerte", "gravite", "cree_le")
    search_fields = ("rumeur__titre", "expression_detectee", "explication")
    readonly_fields = ("cree_le",)
    autocomplete_fields = ("rumeur",)


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

@admin.register(RapportVerification)
class RapportVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "rumeur",
        "score_credibilite",
        "niveau_risque",
        "genere_le",
    )
    list_filter = ("niveau_risque", "genere_le")
    search_fields = ("rumeur__titre", "resume")
    readonly_fields = ("genere_le",)
    autocomplete_fields = ("rumeur",)
