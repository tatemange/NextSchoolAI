from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser


# ===== RÔLES ET UTILISATEURS =====

class Role(models.Model):
    libelle = models.CharField(max_length=50)

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name = "Rôle"


class Utilisateur(AbstractUser):
    """
    On étend le modèle utilisateur de Django
    pour ajouter nos champs personnalisés
    """
    sexe = models.CharField(max_length=10, blank=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='utilisateurs_custom',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='utilisateurs_custom',
        blank=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Utilisateur"


# ===== CLASSIFICATION DES DOCUMENTS =====

class Niveau(models.Model):
    libelle_niveau = models.CharField(max_length=50)

    def __str__(self):
        return self.libelle_niveau

    class Meta:
        verbose_name = "Niveau scolaire"


class Classe(models.Model):
    libelle_classe = models.CharField(max_length=50)
    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='classes'
    )

    def __str__(self):
        return self.libelle_classe

    class Meta:
        verbose_name = "Classe"


class Matiere(models.Model):
    nom_matiere = models.CharField(max_length=100)

    def __str__(self):
        return self.nom_matiere

    class Meta:
        verbose_name = "Matière"


class Licence(models.Model):
    description = models.TextField()
    URL_legal = models.URLField(blank=True)
    nomLicence = models.CharField(max_length=100)

    def __str__(self):
        return self.nomLicence

    class Meta:
        verbose_name = "Licence"


# ===== DOCUMENTS =====

class Document(models.Model):
    STATUT_AI_CHOICES = [
        ('en_attente', 'En attente'),
        ('analyse', 'Analysé'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]
    STATUT_DOC_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publie', 'Publié'),
        ('archive', 'Archivé'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url_fichier = models.FileField(upload_to='documents/')
    annee_academique = models.CharField(max_length=9, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)
    statut_ai = models.CharField(
        max_length=20,
        choices=STATUT_AI_CHOICES,
        default='en_attente'
    )
    statut_humain = models.BooleanField(default=False)
    statut_doc = models.CharField(
        max_length=20,
        choices=STATUT_DOC_CHOICES,
        default='brouillon'
    )
    version = models.IntegerField(default=1)
    poids_fichier = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    date_validation = models.DateTimeField(blank=True, null=True)
    commentaire_validateur = models.TextField(blank=True)

    # Relations
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    classe = models.ForeignKey(
        Classe,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents'
    )
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents'
    )
    licence = models.ForeignKey(
        Licence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )

    def __str__(self):
        return self.titre

    class Meta:
        verbose_name = "Document"


# ===== TYPES DE DOCUMENTS (héritage du MCD) =====

class Cours(Document):
    numero_chapitre = models.IntegerField(blank=True, null=True)
    est_resume_officiel = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Cours"


class Epreuve(Document):
    session_examen = models.CharField(max_length=50, blank=True)
    duree = models.IntegerField(blank=True, null=True)
    type_examen = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Épreuve"


class Livre(Document):
    isbn = models.CharField(max_length=20, blank=True)
    maison_edition = models.CharField(max_length=100, blank=True)
    nombre_pages = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Livre"


# ===== INTERACTION IA =====

class InteractionIA(models.Model):
    TYPE_CHOICES = [
        ('resume', 'Résumé'),
        ('qcm', 'QCM'),
        ('correction', 'Correction'),
        ('explication', 'Explication'),
    ]

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='interactions_ia'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='interactions_ia',
        null=True,
        blank=True
    )
    type_interaction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_action = models.DateTimeField(auto_now_add=True)
    prompt_utilisateur = models.TextField(blank=True)
    contenu_genere = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type_interaction} — {self.utilisateur}"

    class Meta:
        verbose_name = "Interaction IA"