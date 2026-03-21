"""
Vues de l'application ia — NextSchoolAI.
Résumé automatique, assistance IA.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from documents.models import Document, Activite
from ia.services import IAService, extraire_texte
from ia.models import InteractionIA


@login_required
def resumer_document(request, doc_pk):
    """Génère un résumé IA d'un document et l'affiche à l'utilisateur."""
    document = get_object_or_404(Document, pk=doc_pk, statut_doc='publie')

    # Vérification si un résumé récent existe déjà (cache 24h)
    from django.utils import timezone
    from datetime import timedelta
    interaction_existante = InteractionIA.objects.filter(
        document=document,
        type_interaction='resume',
        succes=True,
        date_action__gte=timezone.now() - timedelta(hours=24)
    ).first()

    resume = None
    if interaction_existante:
        resume = interaction_existante.contenu_genere
    elif request.method == 'POST':
        # Extraction du texte
        filepath = document.url_fichier.path
        texte    = extraire_texte(filepath)

        if not texte:
            messages.error(request, _("Impossible d'extraire le texte de ce document."))
            return redirect('documents:detail', pk=doc_pk)

        resultat = IAService.generer_resume(texte, titre=document.titre)

        interaction = InteractionIA.objects.create(
            utilisateur=request.user,
            document=document,
            type_interaction='resume',
            moteur_ia=resultat.get('moteur', 'gemini'),
            contenu_genere=resultat.get('contenu', ''),
            duree_secondes=int(resultat.get('duree', 0)),
            tokens_utilises=resultat.get('tokens'),
            succes=resultat['succes'],
            message_erreur=resultat.get('erreur', ''),
        )

        Activite.objects.create(
            utilisateur=request.user,
            document=document,
            type_action='resume',
        )

        if resultat['succes']:
            resume = resultat['contenu']
        else:
            messages.error(request, _("Erreur lors de la génération du résumé."))

    return render(request, 'ia/resume.html', {
        'document':   document,
        'resume':     resume,
        'titre_page': f"Résumé IA — {document.titre}",
    })


@login_required
@require_POST
def assister_ia(request):
    """
    Endpoint AJAX pour l'assistant IA (questions libres).
    Retourne une réponse JSON.
    """
    question = request.POST.get('question', '').strip()
    doc_pk   = request.POST.get('document_pk')

    if not question:
        return JsonResponse({'succes': False, 'erreur': 'Question vide.'})

    contexte = ""
    document = None
    if doc_pk:
        try:
            document = Document.objects.get(pk=doc_pk, statut_doc='publie')
            chemin   = document.url_fichier.path
            contexte = extraire_texte(chemin)[:3000]
        except Document.DoesNotExist:
            pass

    resultat = IAService.generer_explication(question, contexte=contexte)

    InteractionIA.objects.create(
        utilisateur=request.user,
        document=document,
        type_interaction='explication',
        moteur_ia=resultat.get('moteur', 'gemini'),
        prompt_utilisateur=question,
        contenu_genere=resultat.get('contenu', ''),
        duree_secondes=int(resultat.get('duree', 0)),
        succes=resultat['succes'],
        message_erreur=resultat.get('erreur', ''),
    )

    return JsonResponse({
        'succes':  resultat['succes'],
        'contenu': resultat.get('contenu', ''),
        'erreur':  resultat.get('erreur', ''),
    })
