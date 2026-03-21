"""
Formulaires de l'application documents — NextSchoolAI.
Upload de documents, filtrage, évaluations.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Document, Cours, Epreuve, Livre, Evaluer, Matiere, Classe, Niveau


class UploadDocumentForm(forms.ModelForm):
    """
    Formulaire d'upload d'un document.
    Le type concret (Cours, Epreuve, Livre) est déterminé
    par la vue après soumission.
    """
    TYPE_DOC_CHOICES = [
        ('cours',   _('Cours / TD / Résumé')),
        ('epreuve', _('Épreuve / Sujet d\'examen')),
        ('livre',   _('Livre / Manuel')),
    ]
    type_document = forms.ChoiceField(
        choices=TYPE_DOC_CHOICES,
        label=_("Type de document"),
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'type_document'})
    )

    class Meta:
        model  = Document
        fields = ('titre', 'description', 'url_fichier', 'annee_academique', 'classe', 'matiere', 'licence')
        widgets = {
            'titre':           forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Titre du document'}),
            'description':     forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Description courte (optionnel)'}),
            'url_fichier':     forms.ClearableFileInput(attrs={'class': 'form-file', 'accept': '.pdf,.jpg,.jpeg,.png,.webp'}),
            'annee_academique':forms.TextInput(attrs={'class': 'form-input', 'placeholder': '2024-2025'}),
            'classe':          forms.Select(attrs={'class': 'form-input'}),
            'matiere':         forms.Select(attrs={'class': 'form-input'}),
            'licence':         forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['annee_academique'].required = False
        self.fields['classe'].required  = False
        self.fields['matiere'].required = False
        self.fields['licence'].required = False

    def clean_url_fichier(self):
        fichier = self.cleaned_data.get('url_fichier')
        if fichier:
            taille_mo = fichier.size / (1024 * 1024)
            if taille_mo > 50:
                raise forms.ValidationError(
                    _("Le fichier ne doit pas dépasser 50 Mo. Taille actuelle : %(size).1f Mo.") % {'size': taille_mo}
                )
        return fichier


class FiltreDocumentForm(forms.Form):
    """
    Formulaire de filtrage/recherche des documents.
    Utilisé sur la page de liste des documents.
    """
    q       = forms.CharField(
        required=False,
        label=_("Recherche"),
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'placeholder': _("Rechercher un document, matière, auteur...")
        })
    )
    matiere = forms.ModelChoiceField(
        queryset=Matiere.objects.all(),
        required=False,
        label=_("Matière"),
        empty_label=_("Toutes les matières"),
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    niveau  = forms.ModelChoiceField(
        queryset=Niveau.objects.all(),
        required=False,
        label=_("Niveau"),
        empty_label=_("Tous les niveaux"),
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    classe  = forms.ModelChoiceField(
        queryset=Classe.objects.select_related('niveau').all(),
        required=False,
        label=_("Classe"),
        empty_label=_("Toutes les classes"),
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    annee   = forms.CharField(
        required=False,
        label=_("Année académique"),
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '2024-2025'})
    )
    type_doc = forms.ChoiceField(
        choices=[
            ('', _('Tous les types')),
            ('cours',   _('Cours')),
            ('epreuve', _('Épreuves')),
            ('livre',   _('Livres')),
        ],
        required=False,
        label=_("Type"),
        widget=forms.Select(attrs={'class': 'form-input'})
    )


class EvaluationForm(forms.ModelForm):
    """Formulaire de notation et commentaire d'un document."""
    class Meta:
        model  = Evaluer
        fields = ('note', 'commentaire')
        widgets = {
            'note':        forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 5}),
            'commentaire': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Votre avis sur ce document...'}),
        }
