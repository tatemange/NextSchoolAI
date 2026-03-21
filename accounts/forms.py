"""
Formulaires de l'application accounts — NextSchoolAI.
Inscription, connexion, modification du profil.
"""

from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur, Role


class InscriptionForm(forms.ModelForm):
    """Formulaire d'inscription d'un nouvel utilisateur."""
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minimum 8 caractères',
            'autocomplete': 'new-password',
        }),
        min_length=8,
    )
    password2 = forms.CharField(
        label=_("Confirmez le mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Répétez le mot de passe',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model  = Utilisateur
        fields = ('first_name', 'last_name', 'username', 'email', 'avatar', 'sexe', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'}),
            'username':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': "Nom d'utilisateur"}),
            'email':      forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
            'avatar':     forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'sexe':       forms.Select(attrs={'class': 'form-input'}),
            'role':       forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # N'afficher que les rôles accessibles à l'inscription (pas admin)
        self.fields['role'].queryset = Role.objects.exclude(code='admin')
        self.fields['role'].empty_label = None
        
        # Par défaut, sélectionner 'apprenant'
        try:
            apprenant = Role.objects.get(code='apprenant')
            self.fields['role'].initial = apprenant
        except Role.DoesNotExist:
            pass
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        self.fields['email'].required      = True

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if Utilisateur.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Cette adresse email est déjà utilisée."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if Utilisateur.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Ce nom d'utilisateur est déjà pris."))
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("Les deux mots de passe ne correspondent pas."))
        return cleaned_data

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.set_password(self.cleaned_data['password1'])
        utilisateur.email = self.cleaned_data['email'].lower()
        if commit:
            utilisateur.save()
        return utilisateur


class ConnexionForm(forms.Form):
    """Formulaire de connexion avec identifiant (username ou email) + mot de passe."""
    identifiant = forms.CharField(
        label=_("Nom d'utilisateur ou email"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': "Nom d'utilisateur ou adresse email",
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password',
        }),
    )
    se_souvenir = forms.BooleanField(
        required=False,
        label=_("Rester connecté"),
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        identifiant  = cleaned_data.get('identifiant', '').strip()
        password     = cleaned_data.get('password', '')

        if not identifiant or not password:
            return cleaned_data

        # Tentative avec username
        utilisateur = authenticate(username=identifiant, password=password)

        # Tentative avec email si username échoue
        if utilisateur is None:
            try:
                user_obj = Utilisateur.objects.get(email=identifiant.lower())
                utilisateur = authenticate(username=user_obj.username, password=password)
            except Utilisateur.DoesNotExist:
                pass

        if utilisateur is None:
            raise forms.ValidationError(
                _("Identifiant ou mot de passe incorrect. Vérifiez vos informations.")
            )
        if not utilisateur.is_active:
            raise forms.ValidationError(
                _("Ce compte est désactivé. Contactez l'administrateur.")
            )

        cleaned_data['utilisateur'] = utilisateur
        return cleaned_data


class ProfilForm(forms.ModelForm):
    """Formulaire de modification du profil utilisateur."""
    class Meta:
        model  = Utilisateur
        fields = ('first_name', 'last_name', 'email', 'avatar', 'sexe')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-input'}),
            'email':      forms.EmailInput(attrs={'class': 'form-input'}),
            'avatar':     forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'sexe':       forms.Select(attrs={'class': 'form-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = Utilisateur.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("Cette adresse email est déjà utilisée."))
        return email
