"""
Admin de l'application documents — NextSchoolAI.
Interface d'administration avec actions de modération (valider/rejeter).
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Niveau, Classe, Matiere, Licence,
    Document, Cours, Epreuve, Livre,
    Images, Activite, Evaluer
)


# =============================================================================
# CLASSIFICATION
# =============================================================================

@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display  = ('id', 'libelle_niveau')
    search_fields = ('libelle_niveau',)


class ClasseInline(admin.TabularInline):
    model  = Classe
    extra  = 0
    fields = ('libelle_classe',)


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display  = ('libelle_classe', 'niveau')
    list_filter   = ('niveau',)
    search_fields = ('libelle_classe',)


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display  = ('id', 'nom_matiere')
    search_fields = ('nom_matiere',)


@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display  = ('nom_licence', 'url_legal')
    search_fields = ('nom_licence',)


# =============================================================================
# DOCUMENTS
# =============================================================================

class ImagesInline(admin.TabularInline):
    model  = Images
    extra  = 0
    fields = ('titre', 'url_fichier', 'statut_doc')
    readonly_fields = ('date_upload',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ('titre', 'utilisateur', 'matiere', 'classe', 'statut_doc', 'statut_ia', 'date_upload')
    list_filter   = ('statut_doc', 'statut_ia', 'statut_humain', 'matiere', 'classe__niveau')
    search_fields = ('titre', 'description', 'utilisateur__username', 'utilisateur__email')
    readonly_fields = ('date_upload', 'date_validation')
    date_hierarchy  = 'date_upload'
    inlines         = [ImagesInline]

    fieldsets = (
        (_('Informations de base'), {
            'fields': ('titre', 'description', 'url_fichier', 'annee_academique', 'licence')
        }),
        (_('Classification'), {
            'fields': ('utilisateur', 'classe', 'matiere')
        }),
        (_('Validation'), {
            'fields': ('statut_ia', 'statut_humain', 'statut_doc', 'commentaire_validateur', 'date_validation')
        }),
        (_('Métadonnées'), {
            'fields': ('poids_fichier', 'version', 'date_upload'),
            'classes': ('collapse',)
        }),
    )

    actions = ['valider_documents', 'rejeter_documents', 'archiver_documents']

    @admin.action(description=_("✅ Valider et publier les documents sélectionnés"))
    def valider_documents(self, request, queryset):
        for doc in queryset:
            doc.marquer_publie(
                validateur=request.user,
                commentaire=f"Validé en masse par {request.user.username}"
            )
        self.message_user(request, f"{queryset.count()} document(s) publié(s).")

    @admin.action(description=_("❌ Rejeter les documents sélectionnés"))
    def rejeter_documents(self, request, queryset):
        for doc in queryset:
            doc.rejeter(commentaire=f"Rejeté en masse par {request.user.username}")
        self.message_user(request, f"{queryset.count()} document(s) rejeté(s).")

    @admin.action(description=_("📦 Archiver les documents sélectionnés"))
    def archiver_documents(self, request, queryset):
        mis_a_jour = queryset.update(statut_doc='archive')
        self.message_user(request, f"{mis_a_jour} document(s) archivé(s).")


@admin.register(Cours)
class CoursAdmin(DocumentAdmin):
    list_display = ('titre', 'numero_chapitre', 'titre_chapitre', 'est_resume_officiel', 'statut_doc')
    fieldsets = DocumentAdmin.fieldsets + (
        (_('Infos cours'), {
            'fields': ('numero_chapitre', 'titre_chapitre', 'est_resume_officiel')
        }),
    )


@admin.register(Epreuve)
class EpreuveAdmin(DocumentAdmin):
    list_display = ('titre', 'type_examen', 'session_examen', 'duree', 'statut_doc')
    list_filter  = DocumentAdmin.list_filter + ('type_examen',)
    fieldsets = DocumentAdmin.fieldsets + (
        (_('Infos épreuve'), {
            'fields': ('type_examen', 'session_examen', 'duree')
        }),
    )


@admin.register(Livre)
class LivreAdmin(DocumentAdmin):
    list_display = ('titre', 'isbn', 'maison_edition', 'nombre_pages', 'statut_doc')
    fieldsets = DocumentAdmin.fieldsets + (
        (_('Infos livre'), {
            'fields': ('isbn', 'maison_edition', 'nombre_pages')
        }),
    )


@admin.register(Evaluer)
class EvaluerAdmin(admin.ModelAdmin):
    list_display  = ('utilisateur', 'document', 'note', 'date_avis')
    list_filter   = ('note',)
    search_fields = ('utilisateur__username', 'document__titre')
    readonly_fields = ('date_avis',)


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display    = ('utilisateur', 'document', 'type_action', 'date_action', 'ip_adresse')
    list_filter     = ('type_action',)
    search_fields   = ('utilisateur__username', 'document__titre')
    readonly_fields = ('date_action',)
    date_hierarchy  = 'date_action'
