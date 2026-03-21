"""
Vues de l'application quiz — NextSchoolAI.
Génération, passage, soumission et correction de QCM.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from documents.models import Document, Activite
from ia.models import InteractionIA
from ia.services import IAService, extraire_texte
from .models import Question, OptionReponse, SessionQCM, ReponseSession


# =============================================================================
# GÉNÉRER UN QCM
# =============================================================================

@login_required
def generer_qcm(request, doc_pk):
    """
    Lance la génération d'un QCM à partir d'un document.
    Appel IA → Sauvegarde des questions → Redirection vers le QCM.
    """
    document = get_object_or_404(Document, pk=doc_pk, statut_doc='publie')

    if request.method == 'POST':
        nb_questions = int(request.POST.get('nb_questions', 10))
        nb_questions = max(3, min(nb_questions, 20))

        # Extraction du texte
        filepath = document.url_fichier.path
        texte    = extraire_texte(filepath)

        if not texte or len(texte.strip()) < 100:
            messages.error(request, _("Impossible de générer un QCM : le document ne contient pas assez de texte exploitable."))
            return redirect('documents:detail', pk=doc_pk)

        # Appel au service IA
        resultat = IAService.generer_qcm(texte, nb_questions=nb_questions, titre=document.titre)

        if not resultat['succes'] or not resultat['questions']:
            messages.error(request, _("La génération du QCM a échoué : %(erreur)s") % {'erreur': resultat.get('erreur', 'Erreur inconnue')})
            return redirect('documents:detail', pk=doc_pk)

        # Création de l'interaction IA
        interaction = InteractionIA.objects.create(
            utilisateur=request.user,
            document=document,
            type_interaction='qcm',
            moteur_ia=resultat.get('moteur', 'gemini'),
            contenu_genere=json.dumps(resultat['questions'], ensure_ascii=False),
            duree_secondes=int(resultat.get('duree', 0)),
            tokens_utilises=resultat.get('tokens'),
            succes=True,
        )

        # Création des questions et options
        for q_data in resultat['questions']:
            question = Question.objects.create(
                interaction=interaction,
                matiere=document.matiere,
                enonce=q_data['enonce'],
                points=q_data.get('points', 1),
                explication=q_data.get('explication', ''),
                ordre=q_data.get('ordre', 0),
            )
            for opt in q_data.get('options', []):
                OptionReponse.objects.create(
                    question=question,
                    libelle_option=opt['libelle'],
                    est_correct=opt.get('est_correct', False),
                )

        # Création de la session QCM
        session = SessionQCM.objects.create(
            utilisateur=request.user,
            interaction=interaction,
            document=document,
            nb_questions=len(resultat['questions']),
            score_total=sum(q.get('points', 1) for q in resultat['questions']),
        )

        # Traçabilité activité
        Activite.objects.create(
            utilisateur=request.user,
            document=document,
            type_action='qcm',
        )

        messages.success(request, _("QCM de %(nb)d questions généré avec succès !") % {'nb': len(resultat['questions'])})
        return redirect('quiz:passer', session_pk=session.pk)

    return render(request, 'quiz/generer.html', {
        'document':   document,
        'titre_page': f"Générer un QCM — {document.titre}",
    })


# =============================================================================
# PASSER LE QCM
# =============================================================================

@login_required
def passer_qcm(request, session_pk):
    """
    Page de passage du QCM.
    Affiche les questions une par une ou toutes ensemble.
    """
    session = get_object_or_404(SessionQCM, pk=session_pk, utilisateur=request.user)

    if session.statut == 'termine':
        return redirect('quiz:resultats', session_pk=session.pk)

    questions = Question.objects.filter(
        interaction=session.interaction
    ).prefetch_related('options').order_by('ordre')

    return render(request, 'quiz/passer.html', {
        'session':    session,
        'questions':  questions,
        'titre_page': "Passer le QCM",
    })


# =============================================================================
# SOUMETTRE LE QCM
# =============================================================================

@login_required
@require_POST
def soumettre_qcm(request, session_pk):
    """
    Traitement des réponses soumises par l'utilisateur.
    Calcul du score et mise à jour de la session.
    """
    session = get_object_or_404(SessionQCM, pk=session_pk, utilisateur=request.user)

    if session.statut == 'termine':
        return redirect('quiz:resultats', session_pk=session.pk)

    questions   = Question.objects.filter(interaction=session.interaction).prefetch_related('options')
    score       = 0
    reponses_ok = []

    for question in questions:
        option_id = request.POST.get(f'question_{question.pk}')
        if option_id:
            try:
                option = OptionReponse.objects.get(pk=option_id, question=question)
                est_correct = option.est_correct
                if est_correct:
                    score += question.points

                reponse, _ = ReponseSession.objects.get_or_create(
                    session=session,
                    question=question,
                    defaults={
                        'option_choisie': option,
                        'est_correct':    est_correct,
                    }
                )
                reponses_ok.append(reponse)
            except OptionReponse.DoesNotExist:
                pass
        else:
            # Question sans réponse
            ReponseSession.objects.get_or_create(
                session=session,
                question=question,
                defaults={
                    'option_choisie': None,
                    'est_correct':    False,
                }
            )

    # Finalisation de la session
    session.score_obtenu = score
    session.statut       = 'termine'
    session.date_fin     = timezone.now()
    session.save(update_fields=['score_obtenu', 'statut', 'date_fin'])

    messages.success(
        request,
        _("QCM terminé ! Votre score : %(score)d / %(total)d (%(pct)s%%)") % {
            'score': score,
            'total': session.score_total,
            'pct':   session.pourcentage,
        }
    )
    return redirect('quiz:resultats', session_pk=session.pk)


# =============================================================================
# RÉSULTATS
# =============================================================================

@login_required
def resultats_qcm(request, session_pk):
    """Affichage des résultats après soumission du QCM."""
    session = get_object_or_404(SessionQCM, pk=session_pk, utilisateur=request.user)

    reponses = ReponseSession.objects.filter(
        session=session
    ).select_related('question', 'option_choisie').prefetch_related('question__options')

    return render(request, 'quiz/resultats.html', {
        'session':    session,
        'reponses':   reponses,
        'titre_page': f"Résultats — {session.pourcentage}%",
    })


# =============================================================================
# CORRECTION DÉTAILLÉE
# =============================================================================

@login_required
def correction_qcm(request, session_pk):
    """Correction détaillée générée par l'IA (si demandée après le QCM)."""
    session = get_object_or_404(SessionQCM, pk=session_pk, utilisateur=request.user, statut='termine')

    reponses = ReponseSession.objects.filter(
        session=session
    ).select_related('question', 'option_choisie').prefetch_related('question__options')

    return render(request, 'quiz/correction.html', {
        'session':    session,
        'reponses':   reponses,
        'titre_page': "Correction détaillée",
    })


# =============================================================================
# HISTORIQUE DES QCM
# =============================================================================

@login_required
def historique_qcm(request):
    """Historique de toutes les sessions QCM de l'utilisateur."""
    sessions = SessionQCM.objects.filter(
        utilisateur=request.user
    ).select_related('document').order_by('-date_debut')

    return render(request, 'quiz/historique.html', {
        'sessions':   sessions,
        'titre_page': "Mon historique QCM",
    })
