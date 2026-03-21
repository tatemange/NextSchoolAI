"""
Managers personnalisés pour le modèle Utilisateur de NextSchoolAI.
Fournit des méthodes utilitaires pour créer des utilisateurs selon leur rôle.
"""

from django.contrib.auth.models import BaseUserManager


class UtilisateurManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle Utilisateur.
    Remplace le manager par défaut de Django pour contrôler
    la création des utilisateurs selon les rôles définis dans le système.
    """

    def _creer_utilisateur(self, username, email, password, **extra_fields):
        """Méthode interne commune à toutes les créations."""
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire.")
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Crée un utilisateur standard (apprenant par défaut)."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._creer_utilisateur(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Crée un superutilisateur avec tous les droits Django."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

        return self._creer_utilisateur(username, email, password, **extra_fields)

    def apprenants(self):
        """Retourne uniquement les utilisateurs de type apprenant."""
        return self.get_queryset().filter(role__code='apprenant', is_active=True)

    def enseignants(self):
        """Retourne uniquement les utilisateurs de type enseignant."""
        return self.get_queryset().filter(role__code='enseignant', is_active=True)

    def administrateurs(self):
        """Retourne uniquement les administrateurs de la plateforme."""
        return self.get_queryset().filter(role__code='admin', is_active=True)

    def actifs(self):
        """Retourne tous les utilisateurs actifs."""
        return self.get_queryset().filter(is_active=True)
