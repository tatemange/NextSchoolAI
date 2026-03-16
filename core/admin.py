from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Role, Utilisateur, Niveau, Classe,
    Matiere, Licence, Document,
    Cours, Epreuve, Livre, InteractionIA
)

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('sexe', 'role')
        }),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'libelle')

@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('id', 'libelle_niveau')

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('id', 'libelle_classe', 'niveau')

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_matiere')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('titre', 'utilisateur', 'matiere', 'classe', 'statut_doc', 'date_upload')
    list_filter = ('statut_doc', 'statut_ai', 'matiere')
    search_fields = ('titre', 'description')

@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ('titre', 'numero_chapitre', 'est_resume_officiel')

@admin.register(Epreuve)
class EpreuveAdmin(admin.ModelAdmin):
    list_display = ('titre', 'session_examen', 'type_examen', 'duree')

@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'isbn', 'maison_edition', 'nombre_pages')

@admin.register(InteractionIA)
class InteractionIAAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_interaction', 'document', 'date_action')
    list_filter = ('type_interaction',)

@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ('nomLicence', 'description')