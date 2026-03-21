"""
Admin pour l'application ia — NextSchoolAI.
Log de toutes les interactions IA pour audit et amélioration.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import InteractionIA


@admin.register(InteractionIA)
class InteractionIAAdmin(admin.ModelAdmin):
    list_display    = ('utilisateur', 'type_interaction', 'moteur_ia', 'document', 'succes', 'duree_secondes', 'date_action')
    list_filter     = ('type_interaction', 'moteur_ia', 'succes')
    search_fields   = ('utilisateur__username', 'document__titre')
    readonly_fields = ('date_action',)
    date_hierarchy  = 'date_action'
    ordering        = ('-date_action',)

    fieldsets = (
        (_('Interaction'), {
            'fields': ('utilisateur', 'document', 'type_interaction', 'moteur_ia')
        }),
        (_('Contenu'), {
            'fields': ('prompt_utilisateur', 'contenu_genere'),
            'classes': ('collapse',)
        }),
        (_('Performance'), {
            'fields': ('succes', 'message_erreur', 'duree_secondes', 'tokens_utilises', 'date_action')
        }),
    )
