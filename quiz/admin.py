"""
Admin pour l'application quiz — NextSchoolAI.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Question, OptionReponse, SessionQCM, ReponseSession


class OptionReponseInline(admin.TabularInline):
    model  = OptionReponse
    extra  = 4
    fields = ('libelle_option', 'est_correct')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display  = ('enonce_court', 'matiere', 'points', 'ordre')
    list_filter   = ('matiere',)
    search_fields = ('enonce',)
    inlines       = [OptionReponseInline]

    def enonce_court(self, obj):
        return obj.enonce[:80]
    enonce_court.short_description = _("Énoncé")


class ReponseSessionInline(admin.TabularInline):
    model         = ReponseSession
    extra         = 0
    readonly_fields = ('question', 'option_choisie', 'est_correct', 'date_reponse')
    can_delete    = False


@admin.register(SessionQCM)
class SessionQCMAdmin(admin.ModelAdmin):
    list_display    = ('utilisateur', 'document', 'score_obtenu', 'score_total', 'pourcentage', 'statut', 'date_debut')
    list_filter     = ('statut',)
    readonly_fields = ('date_debut', 'date_fin', 'score_obtenu', 'score_total')
    inlines         = [ReponseSessionInline]

    def pourcentage(self, obj):
        return f"{obj.pourcentage}%"
    pourcentage.short_description = _("Résultat")
