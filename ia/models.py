"""
Modèles de l'application ia — NextSchoolAI.

Entité :
- InteractionIA : Log de toutes les interactions entre un utilisateur et le service IA.
  (résumé, QCM, correction, explication)
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class InteractionIA(models.Model):
    """
    Enregistre chaque interaction d'un utilisateur avec le moteur IA.

    Sert à :
    - Tracer et améliorer les réponses IA
    - Lier les QCM générés à leur source documentaire
    - Permettre l'audit et la modération des contenus IA
    """

    TYPE_INTERACTION_CHOICES = [
        ('resume',      _('Résumé automatique')),
        ('qcm',         _('Génération de QCM')),
        ('correction',  _('Correction détaillée')),
        ('explication', _('Explication de cours')),
    ]

    MOTEUR_IA_CHOICES = [
        ('gemini',       'Google Gemini'),
        ('huggingface',  'Hugging Face'),
        ('deepseek',     'DeepSeek R1'),
        ('local',        'Modèle local'),
    ]

    # --- Qui a interagi ---
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interactions_ia',
        verbose_name=_("Utilisateur")
    )

    # --- Sur quel document ---
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interactions_ia',
        verbose_name=_("Document source")
    )

    # --- Nature de l'interaction ---
    type_interaction = models.CharField(
        max_length=20,
        choices=TYPE_INTERACTION_CHOICES,
        verbose_name=_("Type d'interaction"),
        db_index=True
    )
    moteur_ia = models.CharField(
        max_length=20,
        choices=MOTEUR_IA_CHOICES,
        default='gemini',
        verbose_name=_("Moteur IA utilisé")
    )

    # --- Contenu ---
    prompt_utilisateur = models.TextField(
        blank=True,
        verbose_name=_("Prompt envoyé à l'IA")
    )
    contenu_genere = models.TextField(
        blank=True,
        verbose_name=_("Contenu généré par l'IA")
    )

    # --- Métadonnées ---
    date_action    = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))
    duree_secondes = models.PositiveSmallIntegerField(
        blank=True, null=True,
        verbose_name=_("Durée de génération (s)")
    )
    tokens_utilises = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("Tokens utilisés")
    )
    succes = models.BooleanField(
        default=True,
        verbose_name=_("Succès")
    )
    message_erreur = models.TextField(
        blank=True,
        verbose_name=_("Message d'erreur (si échec)")
    )

    def __str__(self):
        return f"{self.get_type_interaction_display()} — {self.utilisateur} — {self.date_action.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name        = _("Interaction IA")
        verbose_name_plural = _("Interactions IA")
        ordering            = ['-date_action']
        indexes             = [
            models.Index(fields=['utilisateur', 'type_interaction']),
            models.Index(fields=['document', 'type_interaction']),
            models.Index(fields=['type_interaction', 'succes']),
        ]
