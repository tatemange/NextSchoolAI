"""
Modèles de l'application quiz — NextSchoolAI.

Entités :
- Question       : Question QCM liée à un document et une matière
- OptionReponse  : Options de réponse pour une question
- SessionQCM     : Session de passage d'un QCM par un utilisateur
- ReponseSession : Réponse donnée par l'utilisateur à chaque question
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


# =============================================================================
# QUESTION ET OPTIONS
# =============================================================================

class Question(models.Model):
    """
    Question de QCM générée par l'IA ou créée manuellement.
    Liée à une interaction IA et à une matière.
    """
    # La relation vers InteractionIA est définie via string pour éviter
    # les imports circulaires avec l'app ia.
    interaction = models.ForeignKey(
        'ia.InteractionIA',
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("Interaction IA source"),
        null=True,
        blank=True
    )
    matiere = models.ForeignKey(
        'documents.Matiere',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name=_("Matière")
    )
    enonce  = models.TextField(verbose_name=_("Énoncé de la question"))
    points  = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("Points")
    )
    explication = models.TextField(
        blank=True,
        verbose_name=_("Explication de la réponse"),
        help_text=_("Correction détaillée générée par l'IA")
    )
    ordre = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Ordre dans le QCM")
    )

    def __str__(self):
        return self.enonce[:80]

    @property
    def bonne_reponse(self):
        """Retourne la (les) option(s) correcte(s) de la question."""
        return self.options.filter(est_correct=True)

    class Meta:
        verbose_name        = _("Question")
        verbose_name_plural = _("Questions")
        ordering            = ['ordre', 'id']


class OptionReponse(models.Model):
    """
    Option de réponse pour une question de QCM.
    Une seule option doit être correcte par question (QCM simple).
    """
    question      = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("Question")
    )
    libelle_option = models.TextField(verbose_name=_("Texte de l'option"))
    est_correct    = models.BooleanField(
        default=False,
        verbose_name=_("Est la bonne réponse")
    )

    def __str__(self):
        statut = "✓" if self.est_correct else "✗"
        return f"[{statut}] {self.libelle_option[:60]}"

    class Meta:
        verbose_name        = _("Option de réponse")
        verbose_name_plural = _("Options de réponse")


# =============================================================================
# SESSION QCM (PASSAGE D'UN QCM PAR UN UTILISATEUR)
# =============================================================================

class SessionQCM(models.Model):
    """
    Représente une tentative de passage de QCM par un utilisateur.
    Stocke le score final et les métadonnées de session.
    """
    STATUT_CHOICES = [
        ('en_cours',  _('En cours')),
        ('termine',   _('Terminé')),
        ('abandonne', _('Abandonné')),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions_qcm',
        verbose_name=_("Utilisateur")
    )
    interaction = models.ForeignKey(
        'ia.InteractionIA',
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_("Interaction IA (QCM source)"),
        null=True,
        blank=True
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions_qcm',
        verbose_name=_("Document source")
    )
    date_debut  = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de début"))
    date_fin    = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de fin"))
    statut      = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_cours',
        verbose_name=_("Statut")
    )
    score_obtenu    = models.PositiveSmallIntegerField(default=0, verbose_name=_("Score obtenu"))
    score_total     = models.PositiveSmallIntegerField(default=0, verbose_name=_("Score total possible"))
    nb_questions    = models.PositiveSmallIntegerField(default=0, verbose_name=_("Nombre de questions"))

    def __str__(self):
        return f"Session QCM de {self.utilisateur} — {self.score_obtenu}/{self.score_total}"

    @property
    def pourcentage(self):
        """Calcule le pourcentage de réussite."""
        if self.score_total == 0:
            return 0
        return round((self.score_obtenu / self.score_total) * 100, 1)

    @property
    def mention(self):
        """Retourne la mention selon le pourcentage."""
        pct = self.pourcentage
        if pct >= 90:
            return "Excellent"
        elif pct >= 75:
            return "Bien"
        elif pct >= 60:
            return "Assez bien"
        elif pct >= 50:
            return "Passable"
        return "Insuffisant"

    class Meta:
        verbose_name        = _("Session QCM")
        verbose_name_plural = _("Sessions QCM")
        ordering            = ['-date_debut']
        indexes             = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['document', 'statut']),
        ]


class ReponseSession(models.Model):
    """
    Réponse donnée par l'utilisateur à une question lors d'une session QCM.
    """
    session    = models.ForeignKey(
        SessionQCM,
        on_delete=models.CASCADE,
        related_name='reponses',
        verbose_name=_("Session QCM")
    )
    question   = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='reponses_session',
        verbose_name=_("Question")
    )
    option_choisie = models.ForeignKey(
        OptionReponse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reponses_session',
        verbose_name=_("Option choisie")
    )
    est_correct = models.BooleanField(default=False, verbose_name=_("Réponse correcte"))
    date_reponse = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))

    def __str__(self):
        statut = "✓" if self.est_correct else "✗"
        return f"[{statut}] {self.session.utilisateur} → Q{self.question.ordre}"

    class Meta:
        verbose_name        = _("Réponse de session")
        verbose_name_plural = _("Réponses de session")
        unique_together     = [('session', 'question')]
