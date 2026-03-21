"""
Modèles de l'application documents — NextSchoolAI.

Entités :
- Niveau, Classe, Matiere   : Classification scolaire
- Licence                    : Droits d'auteur des documents
- Document (abstrait)        : Base commune
- Cours, Epreuve, Livre      : Types concrets de documents
- Images                     : Médias associés aux documents
- Activite                   : Traçabilité des consultations/téléchargements
- Evaluer                    : Notations et commentaires utilisateurs
"""

import os
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator


# =============================================================================
# CLASSIFICATION SCOLAIRE
# =============================================================================

class Niveau(models.Model):
    """Niveau scolaire (ex : Lycée, Université, Primaire)."""
    libelle_niveau = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Libellé du niveau")
    )

    def __str__(self):
        return self.libelle_niveau

    class Meta:
        verbose_name        = _("Niveau scolaire")
        verbose_name_plural = _("Niveaux scolaires")
        ordering            = ['libelle_niveau']


class Classe(models.Model):
    """Classe scolaire rattachée à un niveau (ex : Terminale C, Licence 2)."""
    libelle_classe = models.CharField(
        max_length=100,
        verbose_name=_("Libellé de la classe")
    )
    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name=_("Niveau")
    )

    def __str__(self):
        return f"{self.libelle_classe} ({self.niveau})"

    class Meta:
        verbose_name        = _("Classe")
        verbose_name_plural = _("Classes")
        ordering            = ['niveau', 'libelle_classe']
        unique_together     = [('libelle_classe', 'niveau')]


class Matiere(models.Model):
    """Matière scolaire (ex : Mathématiques, Histoire-Géographie)."""
    nom_matiere = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Nom de la matière")
    )

    def __str__(self):
        return self.nom_matiere

    class Meta:
        verbose_name        = _("Matière")
        verbose_name_plural = _("Matières")
        ordering            = ['nom_matiere']


# =============================================================================
# LICENCES
# =============================================================================

class Licence(models.Model):
    """
    Licence d'utilisation d'un document.
    Exemples : CC-BY, CC-BY-SA, Tous droits réservés.
    """
    nom_licence = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Nom de la licence")
    )
    description = models.TextField(verbose_name=_("Description"))
    url_legal   = models.URLField(
        blank=True,
        verbose_name=_("URL légale"),
        help_text=_("Lien vers le texte officiel de la licence")
    )

    def __str__(self):
        return self.nom_licence

    class Meta:
        verbose_name        = _("Licence")
        verbose_name_plural = _("Licences")
        ordering            = ['nom_licence']


# =============================================================================
# DOCUMENT (MODÈLE DE BASE — MULTI-TABLE INHERITANCE)
# =============================================================================

def chemin_upload_document(instance, filename):
    """
    Génère un chemin d'upload organisé par type de document et année.
    Ex : documents/cours/2025/mon_fichier.pdf
    """
    ext        = filename.split('.')[-1].lower()
    nom_propre = f"{instance.titre[:50].replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    type_doc   = instance.__class__.__name__.lower()
    annee      = timezone.now().year
    return os.path.join('documents', type_doc, str(annee), nom_propre)


class Document(models.Model):
    """
    Modèle de base pour tous les documents éducatifs de NextSchoolAI.
    Utilise l'héritage multi-tables Django : Cours, Epreuve, Livre héritent de Document.
    """

    # Statuts du pipeline IA
    STATUT_IA_CHOICES = [
        ('en_attente', _('En attente')),
        ('analyse',    _('Analysé')),
        ('valide',     _('Validé par IA')),
        ('rejete',     _('Rejeté par IA')),
    ]

    # Statuts de publication humaine
    STATUT_DOC_CHOICES = [
        ('brouillon', _('Brouillon')),
        ('publie',    _('Publié')),
        ('archive',   _('Archivé')),
        ('rejete',    _('Rejeté')),
    ]

    # --- Informations de base ---
    titre       = models.CharField(max_length=300, verbose_name=_("Titre"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    url_fichier = models.FileField(
        upload_to=chemin_upload_document,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'webp'])],
        verbose_name=_("Fichier")
    )
    annee_academique = models.CharField(
        max_length=9,
        blank=True,
        verbose_name=_("Année académique"),
        help_text=_("Format : 2024-2025")
    )

    # --- Métadonnées automatiques ---
    date_upload  = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'upload"))
    poids_fichier = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Poids (Mo)")
    )
    version = models.PositiveSmallIntegerField(default=1, verbose_name=_("Version"))

    # --- Pipeline de validation ---
    statut_ia = models.CharField(
        max_length=20,
        choices=STATUT_IA_CHOICES,
        default='en_attente',
        verbose_name=_("Statut IA"),
        db_index=True
    )
    statut_humain = models.BooleanField(
        default=False,
        verbose_name=_("Validé humainement")
    )
    statut_doc = models.CharField(
        max_length=20,
        choices=STATUT_DOC_CHOICES,
        default='brouillon',
        verbose_name=_("Statut du document"),
        db_index=True
    )

    # --- Validation ---
    date_validation          = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de validation"))
    commentaire_validateur   = models.TextField(blank=True, verbose_name=_("Commentaire du validateur"))

    # --- Relations ---
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_("Auteur/Uploadeur")
    )
    classe = models.ForeignKey(
        Classe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_("Classe")
    )
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_("Matière")
    )
    licence = models.ForeignKey(
        Licence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_("Licence")
    )

    def __str__(self):
        return self.titre

    def est_publie(self):
        """Document accessible aux apprenants."""
        return self.statut_doc == 'publie' and self.statut_humain

    def marquer_publie(self, validateur=None, commentaire=''):
        """Publie officiellement le document après validation humaine."""
        self.statut_doc            = 'publie'
        self.statut_humain         = True
        self.date_validation       = timezone.now()
        self.commentaire_validateur = commentaire
        self.save(update_fields=[
            'statut_doc', 'statut_humain',
            'date_validation', 'commentaire_validateur'
        ])

    def rejeter(self, commentaire=''):
        """Rejette le document avec un commentaire obligatoire."""
        self.statut_doc             = 'rejete'
        self.statut_humain          = False
        self.commentaire_validateur = commentaire
        self.date_validation        = timezone.now()
        self.save(update_fields=[
            'statut_doc', 'statut_humain',
            'date_validation', 'commentaire_validateur'
        ])

    class Meta:
        verbose_name        = _("Document")
        verbose_name_plural = _("Documents")
        ordering            = ['-date_upload']
        indexes = [
            models.Index(fields=['statut_doc', 'matiere']),
            models.Index(fields=['statut_doc', 'classe']),
            models.Index(fields=['utilisateur', 'statut_doc']),
        ]


# =============================================================================
# TYPES DE DOCUMENTS (HÉRITAGE MULTI-TABLES)
# =============================================================================

class Cours(Document):
    """Document de type Cours — chapitre de cours, TD, résumé officiel."""
    numero_chapitre    = models.PositiveSmallIntegerField(
        blank=True, null=True,
        verbose_name=_("Numéro de chapitre")
    )
    est_resume_officiel = models.BooleanField(
        default=False,
        verbose_name=_("Est un résumé officiel")
    )
    titre_chapitre = models.CharField(
        max_length=200, blank=True,
        verbose_name=_("Titre du chapitre")
    )

    class Meta:
        verbose_name        = _("Cours")
        verbose_name_plural = _("Cours")


class Epreuve(Document):
    """Document de type Épreuve — sujet d'examen, BAC, BTS, devoir."""
    TYPE_EXAMEN_CHOICES = [
        ('BAC',       'BAC'),
        ('BTS',       'BTS'),
        ('PROBATOIRE','Probatoire'),
        ('BEPC',      'BEPC'),
        ('DEVOIR',    'Devoir'),
        ('AUTRE',     'Autre'),
    ]
    session_examen = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Session d'examen"),
        help_text=_("Ex : Juin 2024, Session normale")
    )
    duree = models.PositiveSmallIntegerField(
        blank=True, null=True,
        verbose_name=_("Durée (minutes)")
    )
    type_examen = models.CharField(
        max_length=20,
        choices=TYPE_EXAMEN_CHOICES,
        default='AUTRE',
        verbose_name=_("Type d'examen")
    )

    class Meta:
        verbose_name        = _("Épreuve")
        verbose_name_plural = _("Épreuves")


class Livre(Document):
    """Document de type Livre — manuel, ouvrage de référence."""
    isbn          = models.CharField(max_length=20, blank=True, verbose_name=_("ISBN"))
    maison_edition = models.CharField(max_length=150, blank=True, verbose_name=_("Maison d'édition"))
    nombre_pages   = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Nombre de pages"))

    class Meta:
        verbose_name        = _("Livre")
        verbose_name_plural = _("Livres")


# =============================================================================
# IMAGES ASSOCIÉES AUX DOCUMENTS
# =============================================================================

class Images(models.Model):
    """
    Médias (images, scans) associés à un document.
    Un document peut avoir plusieurs images illustratives.
    """
    document    = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Document")
    )
    url_fichier = models.ImageField(
        upload_to='documents/images/%Y/',
        verbose_name=_("Fichier image")
    )
    titre       = models.CharField(max_length=200, blank=True, verbose_name=_("Titre"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    resolution  = models.CharField(max_length=20, blank=True, verbose_name=_("Résolution"))
    annee_academique = models.CharField(max_length=9, blank=True, verbose_name=_("Année académique"))
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'upload"))
    statut_ai   = models.CharField(max_length=20, default='en_attente', verbose_name=_("Statut IA"))
    statut_humain = models.BooleanField(default=False, verbose_name=_("Validé humainement"))
    statut_doc  = models.CharField(max_length=20, default='brouillon', verbose_name=_("Statut"))
    version     = models.PositiveSmallIntegerField(default=1, verbose_name=_("Version"))
    poids_fichier = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        verbose_name=_("Poids (Mo)")
    )
    date_validation        = models.DateTimeField(blank=True, null=True, verbose_name=_("Date validation"))
    commentaire_validateur = models.TextField(blank=True, verbose_name=_("Commentaire validateur"))

    def __str__(self):
        return self.titre or f"Image #{self.pk} — {self.document}"

    class Meta:
        verbose_name        = _("Image")
        verbose_name_plural = _("Images")
        ordering            = ['-date_upload']


# =============================================================================
# ACTIVITÉ — TRAÇABILITÉ DES CONSULTATIONS
# =============================================================================

class Activite(models.Model):
    """
    Journalise chaque interaction d'un utilisateur avec un document.
    Permet le suivi: consultation, téléchargement, QCM, etc.
    """
    TYPE_ACTION_CHOICES = [
        ('consultation',   _('Consultation')),
        ('telechargement', _('Téléchargement')),
        ('qcm',            _('QCM passé')),
        ('resume',         _('Résumé demandé')),
    ]

    utilisateur       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activites',
        verbose_name=_("Utilisateur")
    )
    document          = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='activites',
        verbose_name=_("Document")
    )
    type_action       = models.CharField(
        max_length=20,
        choices=TYPE_ACTION_CHOICES,
        verbose_name=_("Type d'action")
    )
    date_action       = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))
    ip_adresse        = models.GenericIPAddressField(
        blank=True, null=True,
        verbose_name=_("Adresse IP")
    )
    duree_consultation = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_("Durée de consultation (secondes)")
    )

    def __str__(self):
        return f"{self.utilisateur} — {self.get_type_action_display()} — {self.document}"

    class Meta:
        verbose_name        = _("Activité")
        verbose_name_plural = _("Activités")
        ordering            = ['-date_action']
        indexes             = [
            models.Index(fields=['utilisateur', 'type_action']),
            models.Index(fields=['document', 'type_action']),
        ]


# =============================================================================
# ÉVALUATION — NOTATION ET COMMENTAIRES
# =============================================================================

class Evaluer(models.Model):
    """
    Évaluation d'un document par un utilisateur.
    Note de 1 à 5 + commentaire libre.
    """
    utilisateur  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_("Utilisateur")
    )
    document     = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_("Document")
    )
    note         = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Note (1–5)")
    )
    commentaire  = models.TextField(blank=True, verbose_name=_("Commentaire"))
    date_avis    = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))

    def __str__(self):
        return f"{self.utilisateur} → {self.document} ({self.note}/5)"

    class Meta:
        verbose_name        = _("Évaluation")
        verbose_name_plural = _("Évaluations")
        unique_together     = [('utilisateur', 'document')]
        ordering            = ['-date_avis']
