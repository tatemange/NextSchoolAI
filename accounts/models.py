"""
Modèles de l'application accounts — NextSchoolAI.

Entités :
- Role       : Rôles système (apprenant, enseignant, admin)
- Permission : Droits associés aux rôles
- Utilisateur: Modèle utilisateur étendu (AbstractUser)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import UtilisateurManager


# =============================================================================
# RÔLES ET PERMISSIONS
# =============================================================================

class Role(models.Model):
    """
    Rôle système d'un utilisateur.
    Exemples : apprenant, enseignant, admin.
    """
    CODE_CHOICES = [
        ('apprenant',  'Apprenant'),
        ('enseignant', 'Enseignant'),
        ('admin',      'Administrateur'),
    ]

    code    = models.CharField(max_length=20, choices=CODE_CHOICES, unique=True)
    libelle = models.CharField(max_length=50, verbose_name=_("Libellé"))

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name        = _("Rôle")
        verbose_name_plural = _("Rôles")
        ordering            = ['libelle']


class Permission(models.Model):
    """
    Permission personnalisée liée aux rôles métier de NextSchoolAI.
    Distinct des permissions Django natives.
    """
    code_permission = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Code permission"),
        help_text=_("Ex : peut_uploader_document, peut_valider_document")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    roles       = models.ManyToManyField(
        Role,
        related_name='permissions',
        blank=True,
        verbose_name=_("Rôles associés")
    )

    def __str__(self):
        return self.code_permission

    class Meta:
        verbose_name        = _("Permission")
        verbose_name_plural = _("Permissions")
        ordering            = ['code_permission']


# =============================================================================
# UTILISATEUR
# =============================================================================

class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé de NextSchoolAI.
    Étend AbstractUser pour ajouter : rôle, sexe, date_inscription.

    Champs hérités d'AbstractUser (réutilisés) :
    - first_name, last_name, email, username, is_active, date_joined
    - password (hashé automatiquement), is_staff, is_superuser
    """

    SEXE_CHOICES = [
        ('M', _('Masculin')),
        ('F', _('Féminin')),
        ('A', _('Autre')),
    ]

    THEME_CHOICES = [
        ('brownie',  'Brownie (chaud & sombre)'),
        ('midnight', 'Midnight (noir profond)'),
        ('arctic',   'Arctic (blanc épuré)'),
        ('forest',   'Forest (vert sombre)'),
        ('ocean',    'Ocean (bleu profond)'),
        ('rose',     'Rose (mauve chaud)'),
        ('noir',     'Noir (contraste élevé)'),
    ]

    # Informations personnelles supplémentaires
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name=_("Photo de profil")
    )
    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES,
        blank=True,
        verbose_name=_("Sexe")
    )
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='brownie',
        verbose_name=_("Thème visuel")
    )

    # Rôle fonctionnel dans NextSchoolAI
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs',
        verbose_name=_("Rôle")
    )

    # Résolution du conflit de related_name avec les groupes/permissions Django
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='nextschool_utilisateurs',
        blank=True,
        verbose_name=_("Groupes"),
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='nextschool_utilisateurs',
        blank=True,
        verbose_name=_("Permissions utilisateur"),
    )

    # Manager personnalisé
    objects = UtilisateurManager()

    class Meta:
        verbose_name        = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        ordering            = ['last_name', 'first_name']

    def __str__(self):
        nom_complet = self.get_full_name()
        return nom_complet if nom_complet.strip() else self.username

    # ------------------------------------------------------------------
    # Propriétés de commodité
    # ------------------------------------------------------------------

    @property
    def est_apprenant(self):
        """Vérifie si l'utilisateur est un apprenant."""
        return self.role and self.role.code == 'apprenant'

    @property
    def est_enseignant(self):
        """Vérifie si l'utilisateur est un enseignant."""
        return self.role and self.role.code == 'enseignant'

    @property
    def est_admin(self):
        """Vérifie si l'utilisateur est administrateur NextSchoolAI."""
        return self.is_superuser or (self.role and self.role.code == 'admin')

    def a_permission(self, code_permission: str) -> bool:
        """
        Vérifie si l'utilisateur possède une permission métier spécifique
        via son rôle.
        """
        if self.est_admin:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(code_permission=code_permission).exists()
