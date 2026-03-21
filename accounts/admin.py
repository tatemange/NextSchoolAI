"""
Admin de l'application accounts — NextSchoolAI.
Interface d'administration pour les utilisateurs, rôles et permissions.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Role, Permission, Utilisateur


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ('code', 'libelle')
    search_fields = ('code', 'libelle')
    ordering      = ('libelle',)


class PermissionInline(admin.TabularInline):
    model  = Permission.roles.through
    extra  = 0
    verbose_name        = _("Permission associée")
    verbose_name_plural = _("Permissions associées")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display  = ('code_permission', 'description')
    search_fields = ('code_permission', 'description')
    filter_horizontal = ('roles',)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display  = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_staff', 'sexe')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering      = ('last_name', 'first_name')

    # Ajout de nos champs personnalisés dans le formulaire d'édition
    fieldsets = UserAdmin.fieldsets + (
        (_('Informations NextSchoolAI'), {
            'fields': ('sexe', 'role'),
        }),
    )

    # Ajout de nos champs dans le formulaire de création
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Informations supplémentaires'), {
            'fields': ('email', 'first_name', 'last_name', 'sexe', 'role'),
        }),
    )

    actions = ['activer_utilisateurs', 'desactiver_utilisateurs']

    @admin.action(description=_("Activer les utilisateurs sélectionnés"))
    def activer_utilisateurs(self, request, queryset):
        mise_a_jour = queryset.update(is_active=True)
        self.message_user(request, f"{mise_a_jour} utilisateur(s) activé(s).")

    @admin.action(description=_("Désactiver les utilisateurs sélectionnés"))
    def desactiver_utilisateurs(self, request, queryset):
        mise_a_jour = queryset.update(is_active=False)
        self.message_user(request, f"{mise_a_jour} utilisateur(s) désactivé(s).")
