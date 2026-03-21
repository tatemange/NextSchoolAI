"""
Vues de l'application documents — NextSchoolAI.
Liste, détail, upload, téléchargement et modération.
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import FileResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Document, Cours, Epreuve, Livre, Activite, Evaluer
from .forms import UploadDocumentForm, FiltreDocumentForm, EvaluationForm


# =============================================================================
# LISTE DES DOCUMENTS
# =============================================================================

@login_required
def liste_documents(request):
    """
    Page principale de navigation dans les documents.
    Supporte filtrage par matière, niveau, classe, type, année et recherche textuelle.
    """
    form    = FiltreDocumentForm(request.GET or None)
    queryset = Document.objects.filter(statut_doc='publie').select_related(
        'utilisateur', 'matiere', 'classe', 'classe__niveau', 'licence'
    )

    # Application des filtres
    if form.is_valid():
        q        = form.cleaned_data.get('q')
        matiere  = form.cleaned_data.get('matiere')
        niveau   = form.cleaned_data.get('niveau')
        classe   = form.cleaned_data.get('classe')
        annee    = form.cleaned_data.get('annee')
        type_doc = form.cleaned_data.get('type_doc')

        if q:
            queryset = queryset.filter(
                Q(titre__icontains=q) |
                Q(description__icontains=q) |
                Q(utilisateur__first_name__icontains=q) |
                Q(utilisateur__last_name__icontains=q)
            )
        if matiere:
            queryset = queryset.filter(matiere=matiere)
        if niveau:
            queryset = queryset.filter(classe__niveau=niveau)
        if classe:
            queryset = queryset.filter(classe=classe)
        if annee:
            queryset = queryset.filter(annee_academique__icontains=annee)
        if type_doc == 'cours':
            queryset = queryset.filter(cours__isnull=False)
        elif type_doc == 'epreuve':
            queryset = queryset.filter(epreuve__isnull=False)
        elif type_doc == 'livre':
            queryset = queryset.filter(livre__isnull=False)

    # Pagination (12 documents par page)
    paginator   = Paginator(queryset.order_by('-date_upload'), 12)
    numero_page = request.GET.get('page', 1)
    page        = paginator.get_page(numero_page)

    return render(request, 'documents/liste.html', {
        'page':          page,
        'form':          form,
        'titre_page':    "Bibliothèque de documents",
        'nb_resultats':  queryset.count(),
    })


# =============================================================================
# DÉTAIL D'UN DOCUMENT
# =============================================================================

@login_required
def detail_document(request, pk):
    """
    Page de détail d'un document publié.
    Enregistre l'activité de consultation.
    """
    document = get_object_or_404(Document, pk=pk, statut_doc='publie')

    # Enregistrement de la consultation si utilisateur connecté
    if request.user.is_authenticated:
        Activite.objects.get_or_create(
            utilisateur=request.user,
            document=document,
            type_action='consultation',
            date_action__date=timezone.now().date(),
            defaults={'ip_adresse': _get_ip(request)}
        )

    # Évaluation du document
    evaluation_existante = None
    form_evaluation = None
    if request.user.is_authenticated:
        evaluation_existante = Evaluer.objects.filter(
            utilisateur=request.user, document=document
        ).first()
        if not evaluation_existante:
            form_evaluation = EvaluationForm()

    # Note moyenne
    note_moyenne = Evaluer.objects.filter(document=document).aggregate(
        avg=Avg('note')
    )['avg']

    # Documents similaires (même matière)
    documents_similaires = Document.objects.filter(
        statut_doc='publie',
        matiere=document.matiere
    ).exclude(pk=pk)[:4]

    return render(request, 'documents/detail.html', {
        'document':          document,
        'note_moyenne':      note_moyenne,
        'evaluation':        evaluation_existante,
        'form_evaluation':   form_evaluation,
        'docs_similaires':   documents_similaires,
        'titre_page':        document.titre,
    })


# =============================================================================
# UPLOAD
# =============================================================================

@login_required
def uploader_document(request):
    """
    Upload d'un nouveau document.
    Déclenche automatiquement l'analyse IA après l'enregistrement.
    """
    form = UploadDocumentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        type_doc    = form.cleaned_data.pop('type_document', 'cours')
        fichier     = request.FILES.get('url_fichier')

        # Création du bon sous-type
        if type_doc == 'cours':
            doc = Cours(**{k: v for k, v in form.cleaned_data.items()})
        elif type_doc == 'epreuve':
            doc = Epreuve(**{k: v for k, v in form.cleaned_data.items()})
        else:
            doc = Livre(**{k: v for k, v in form.cleaned_data.items()})

        doc.utilisateur = request.user
        # Calcul du poids en Mo
        if fichier:
            doc.poids_fichier = round(fichier.size / (1024 * 1024), 2)
        doc.save()

        # Lancement de l'analyse IA en arrière-plan (signal)
        messages.success(
            request,
            _("Votre document « %(titre)s » a été uploadé avec succès et est en cours d'analyse IA.") % {
                'titre': doc.titre
            }
        )
        return redirect('documents:detail', pk=doc.pk)

    return render(request, 'documents/upload.html', {
        'form':       form,
        'titre_page': "Uploader un document",
    })


# =============================================================================
# TÉLÉCHARGEMENT
# =============================================================================

@login_required
def telecharger_document(request, pk):
    """
    Téléchargement du fichier d'un document.
    Enregistre l'activité de téléchargement.
    """
    document = get_object_or_404(Document, pk=pk, statut_doc='publie')

    if not document.url_fichier:
        raise Http404("Fichier introuvable.")

    # Enregistrement de l'activité
    Activite.objects.create(
        utilisateur=request.user,
        document=document,
        type_action='telechargement',
        ip_adresse=_get_ip(request)
    )

    chemin_fichier = document.url_fichier.path
    if not os.path.exists(chemin_fichier):
        raise Http404("Le fichier n'existe plus sur le serveur.")

    nom_fichier = os.path.basename(chemin_fichier)
    response = FileResponse(
        open(chemin_fichier, 'rb'),
        as_attachment=True,
        filename=nom_fichier
    )
    return response


# =============================================================================
# ÉVALUATION D'UN DOCUMENT
# =============================================================================

@login_required
@require_POST
def evaluer_document(request, pk):
    """Soumettre ou mettre à jour une évaluation d'un document."""
    document = get_object_or_404(Document, pk=pk, statut_doc='publie')
    form     = EvaluationForm(request.POST)

    if form.is_valid():
        Evaluer.objects.update_or_create(
            utilisateur=request.user,
            document=document,
            defaults={
                'note':        form.cleaned_data['note'],
                'commentaire': form.cleaned_data['commentaire'],
            }
        )
        messages.success(request, _("Votre évaluation a été enregistrée. Merci !"))
    else:
        messages.error(request, _("Erreur dans le formulaire d'évaluation."))

    return redirect('documents:detail', pk=pk)


# =============================================================================
# MES DOCUMENTS (pour les enseignants)
# =============================================================================

@login_required
def mes_documents(request):
    """Liste des documents uploadés par l'utilisateur connecté."""
    documents = Document.objects.filter(
        utilisateur=request.user
    ).order_by('-date_upload')

    paginator   = Paginator(documents, 10)
    numero_page = request.GET.get('page', 1)
    page        = paginator.get_page(numero_page)

    return render(request, 'documents/mes_documents.html', {
        'page':       page,
        'titre_page': "Mes documents",
    })


# =============================================================================
# MODÉRATION (Admin uniquement)
# =============================================================================

@login_required
def moderation(request):
    """File de modération : documents validés par l'IA en attente de validation humaine."""
    if not request.user.est_admin:
        messages.error(request, _("Accès réservé aux administrateurs."))
        return redirect('documents:liste')

    documents_en_attente = Document.objects.filter(
        statut_ia='valide',
        statut_humain=False
    ).select_related('utilisateur', 'matiere', 'classe').order_by('-date_upload')

    return render(request, 'documents/moderation.html', {
        'documents':  documents_en_attente,
        'titre_page': "Modération des documents",
    })


@login_required
@require_POST
def valider_document(request, pk):
    """Valider et publier un document (admin uniquement)."""
    if not request.user.est_admin:
        raise Http404

    document    = get_object_or_404(Document, pk=pk)
    commentaire = request.POST.get('commentaire', '')
    document.marquer_publie(validateur=request.user, commentaire=commentaire)
    messages.success(request, _("Document « %(titre)s » publié avec succès.") % {'titre': document.titre})
    return redirect('documents:moderation')


@login_required
@require_POST
def rejeter_document(request, pk):
    """Rejeter un document avec commentaire (admin uniquement)."""
    if not request.user.est_admin:
        raise Http404

    document    = get_object_or_404(Document, pk=pk)
    commentaire = request.POST.get('commentaire', _("Contenu non conforme."))
    document.rejeter(commentaire=commentaire)
    messages.warning(request, _("Document « %(titre)s » rejeté.") % {'titre': document.titre})
    return redirect('documents:moderation')


# =============================================================================
# UTILITAIRE
# =============================================================================

def _get_ip(request):
    """Récupère l'adresse IP réelle de la requête (proxy compatible)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
